import pyaudio
from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents
import threading
from datetime import datetime
from dotenv import load_dotenv
import pyperclip
from pynput import keyboard
import os
import asyncio
import sys

from elevenlabs.client import ElevenLabs
from elevenlabs import stream as play_audio

from src.spritely.utils.logging import setup_logging
from src.spritely.utils.user_settings import settings
from src.spritely.gui.gui import SpritelyGUI
from src.spritely.utils.audio_utils import check_permissions, FORMAT, CHANNELS, RATE, CHUNK
from src.spritely.core.transcribe_meeting import TranscriberApp
from src.spritely.core.transcribe_field import SpeechTranscriber as FieldTranscriber
from src.spritely.core.invoke_llm import process_prompt

# Move logger initialization to the top, right after imports
logger = setup_logging(__name__)

load_dotenv()
eleven_labs_api_key = os.getenv("ELEVENLABS_API_KEY")

if not eleven_labs_api_key:
    logger.error("ELEVENLABS_API_KEY not found in environment variables")
    raise ValueError("ELEVENLABS_API_KEY is required")

eleven_labs = ElevenLabs(
    api_key=eleven_labs_api_key
    )

""" transcribed audio to cursor/input field """

# Audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
CHUNK = 1024

class SpeechTranscriber:
    def __init__(self):
        logger.info("Initializing SpeechTranscriber")
        self.current_transcription = ""
        self.is_recording = False
        self.audio = None
        self.stream = None
        self.dg_connection = None
        self.audio_thread = None
        self.should_stop = None
        self.loop = asyncio.new_event_loop()
        self.collecting_transcript = False
        self.collected_transcript = []

    def message_handler(self, event, result):
        """Synchronous wrapper for the async message handler"""
        asyncio.run_coroutine_threadsafe(self.on_message(event, result), self.loop)

    async def on_message(self, event, result):
        logger.debug(f"Received message - Event type: {event}")
        logger.debug(f"Result type: {type(result)}")
        try:
            timestamp = datetime.now().isoformat()
            logger.debug(f"Processing transcription at {timestamp}")
            
            if hasattr(result, 'is_final'):
                if result.is_final:
                    transcript = result.channel.alternatives[0].transcript
                    transcript = transcript.strip() + " "
                    
                    if transcript.strip():
                        self.collected_transcript.append(transcript.strip())
                        logger.info(f"Added to transcript: {transcript.strip()}")
                    
                    logger.debug(f"Transcription Details:")
                    logger.debug(f"Transcript: {transcript}")
                    logger.debug(f"Confidence: {result.channel.alternatives[0].confidence:.2f}")
        except Exception as e:
            logger.error(f"Error in transcription: {e}", exc_info=True)

    def start_recording(self):
        if self.is_recording:
            logger.info("Recording already in progress")
            return

        logger.info("Starting recording...")
        self.is_recording = True
        self.current_transcription = ""
        
        # Get clipboard content at start of recording
        clipboard_content = pyperclip.paste()
        if clipboard_content:
            tagged_clipboard = f"<user's_clipboard_content>{clipboard_content}</user's_clipboard_content>"
            self.collected_transcript.append(tagged_clipboard)
            print(f"📎 Added clipboard content: {tagged_clipboard}")
        
        # Play confirmation sound
        logger.info("Playing wake sound")
        audio_stream = eleven_labs.generate(
            text="Spritely here",
            voice="OOjDveYEA7KnRY2FRSmX",
            model="eleven_multilingual_v2",
            stream=True
        )
        play_audio(audio_stream)
        
        # Initialize audio and print device info
        self.audio = pyaudio.PyAudio()
        
        # Use saved microphone preference
        mic_index = settings['microphone_index']
        if mic_index is not None:
            input_device = self.audio.get_device_info_by_index(mic_index)
        else:
            input_device = self.audio.get_default_input_device_info()
            
        logger.info(f"Recording using: {input_device['name']}")
        logger.debug(f"Sample Rate: {input_device['defaultSampleRate']}Hz")
        logger.debug(f"Max Input Channels: {input_device['maxInputChannels']}")
        
        deepgram = DeepgramClient()


        # Start the event loop in a separate thread
        def run_event_loop():
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        threading.Thread(target=run_event_loop, daemon=True).start()
        
        try:
            self.dg_connection = deepgram.listen.websocket.v("1")
            # Use the synchronous wrapper instead of the async method directly
            self.dg_connection.on(LiveTranscriptionEvents.Transcript, self.message_handler)
            print("Deepgram connection created")
        except Exception as e:
            print(f"Failed to create Deepgram connection: {e}")
            return
        
        print("Deepgram connection created")  # Debug line

        # Set up Deepgram connection
        options = LiveOptions(
            model="nova-2",
            encoding="linear16",
            channels=CHANNELS,
            sample_rate=RATE,
            language="en-GB",
            punctuate=True,  # Enable punctuation
            interim_results=False  # Only get final results
        )

        if self.dg_connection.start(options) is False:
            print("Failed to start Deepgram connection")
            return
        
        print("Deepgram connection started successfully")  # Debug line

        # Update stream creation to use selected microphone
        self.stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=settings['microphone_index'],
            frames_per_buffer=CHUNK
        )

        self.should_stop = threading.Event()
        
        # Start audio capture thread
        def capture_audio():
            while not self.should_stop.is_set():
                data = self.stream.read(CHUNK, exception_on_overflow=False)
                # print(f"📢 Sending {len(data)} bytes of audio data")
                self.dg_connection.send(data)

        self.audio_thread = threading.Thread(target=capture_audio)
        self.audio_thread.start()
        print("Recording started!")

    def stop_recording(self):
        if not self.is_recording:
            return

        logger.info("Stopping recording...")
        audio_stream = eleven_labs.generate(
            text="thinking...",
            voice="OOjDveYEA7KnRY2FRSmX",
            model="eleven_multilingual_v2",
            stream=True
        )
        play_audio(audio_stream)
        
        # Process collected transcript with LLM before cleanup
        if self.collected_transcript:
            try:
                full_transcript = " ".join(self.collected_transcript)
                logger.info(f"Processing full transcript: {full_transcript}")
                logger.debug(f"full_transcript type: {type(full_transcript)}")
                
                fut = asyncio.run_coroutine_threadsafe(
                    process_prompt(full_transcript), 
                    self.loop
                )
                response, response_type = fut.result()
                logger.info(f"LLM Response: {response}")
                
            except Exception as e:
                logger.error(f"Error processing with LLM: {e}", exc_info=True)
        
        # Reset collection
        self.collected_transcript = []   
        self.should_stop.set()
        self.audio_thread.join()
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
        self.dg_connection.finish()
        self.is_recording = False
        self.loop.call_soon_threadsafe(self.loop.stop)
        print("Recording stopped!")

class SpritelyApp:
    def __init__(self):
        # Initialize transcribers
        self.transcriber = SpeechTranscriber()
        self.field_transcriber = FieldTranscriber()
        self.meeting_transcriber = TranscriberApp()
        
        # Create and store GUI instance
        self.gui = SpritelyGUI(self.transcriber, self.field_transcriber, self.meeting_transcriber)

def main():
    print("\n✨ Spritely AI is ready to assist✨🧚🏼‍♀️ \n")
    
    # Check if running from shortcut
    if len(sys.argv) > 1 and sys.argv[1] == "--from-shortcut":
        print("Running from keyboard shortcut")
    
    if not check_permissions():
        print("Please grant the required permissions and try again")
        return

    app = SpritelyApp()
    
    # Track pressed keys
    pressed_keys = set()
    
    def on_press(key):
        try:
            key_str = str(key).replace("'", "")
            print(f"Debug - Key string: {key_str}, Pressed keys: {pressed_keys}")
            
            alt_pressed = any(k in pressed_keys for k in [keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r])
            cmd_pressed = keyboard.Key.cmd in pressed_keys
            
            is_k = key_str.lower() == 'k' or '˚' in pressed_keys
            is_l = key_str.lower() == 'l' or '¬' in pressed_keys
            
            if cmd_pressed and alt_pressed:
                if is_k:
                    if not app.transcriber.is_recording:
                        app.transcriber.start_recording()
                        app.gui.update_status("AI Transcription Active", True)
                    else:
                        app.transcriber.stop_recording()
                        app.gui.update_status("Ready", False)
                elif is_l:
                    if not app.field_transcriber.is_recording:
                        app.field_transcriber.start_recording()
                        app.gui.update_status("Field Transcription Active", True)
                    else:
                        app.field_transcriber.stop_recording()
                        app.gui.update_status("Ready", False)
            elif key == keyboard.Key.esc:
                app.transcriber.stop_recording()
                app.field_transcriber.stop_recording()
                app.gui.update_status("Ready", False)
                return False
        except Exception as e:
            print(f"Error handling key press: {e}")
            app.gui.update_status(f"Error: {str(e)}")

    def on_press_track(key):
        if isinstance(key, keyboard.KeyCode):
            pressed_keys.add(key.char)
        else:
            pressed_keys.add(key)
        on_press(key)

    def on_release(key):
        try:
            if isinstance(key, keyboard.KeyCode):
                pressed_keys.discard(key.char)
            else:
                pressed_keys.discard(key)
        except KeyError:
            pass

    # Start keyboard listener in a separate thread
    listener = keyboard.Listener(on_press=on_press_track, on_release=on_release)
    listener.start()
    
    # Start GUI main loop
    app.gui.run()

if __name__ == "__main__":
    main()