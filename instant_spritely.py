import pyaudio
from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents
import threading
from datetime import datetime
from dotenv import load_dotenv
import pyperclip
from pynput import keyboard
import time
import os
import subprocess
import asyncio
import sys
from invoke_llm_pydanic import process_prompt
from utils.logging_config import setup_logger
from user_settings import settings, save_settings
from transcribe_field import SpeechTranscriber as FieldTranscriber
from cartesia_client import CartesiaClient
from gui import SpritelyGUI
from utils.audio_utils import check_permissions, select_microphone, FORMAT, CHANNELS, RATE, CHUNK

load_dotenv()

""" transcribed audio to cursor/input field """

# Audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
CHUNK = 1024

# Initialize logger
logger = setup_logger(__name__)

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
        self.cartesia = CartesiaClient()

    def message_handler(self, event, result):
        """Synchronous wrapper for the async message handler"""
        asyncio.run_coroutine_threadsafe(self.on_message(event, result), self.loop)

    async def on_message(self, event, result):
        logger.debug(f"Received message - Event type: {event}")
        print(f"Result type: {type(result)}")
        try:
            # Create a timestamp for the transcription
            timestamp = datetime.now().isoformat()
            
            print("\n=== Transcription Debug ===")
            print(f"[{timestamp}] Raw result: {result}")
            
            if hasattr(result, 'is_final'):
                if result.is_final:
                    transcript = result.channel.alternatives[0].transcript
                    transcript = transcript.strip() + " "
                    
                    # Simplified collection - always collect while recording
                    if transcript.strip():
                        self.collected_transcript.append(transcript.strip())
                        print(f"📝 Adding to transcript: {transcript.strip()}")
                    
                    # Print debug info
                    print(f"\n🎤 Transcription Details:")
                    print(f"📝 Transcript: {transcript}")
                    print(f"✨ Confidence: {result.channel.alternatives[0].confidence:.2f}")
        except Exception as e:
            logger.error(f"Error in transcription: {e}", exc_info=True)
            import traceback
            traceback.print_exc()

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
        self.cartesia.generate_and_play("Spritely here")
        
        # Initialize audio and print device info
        self.audio = pyaudio.PyAudio()
        
        # Use saved microphone preference
        mic_index = settings['microphone_index']
        if mic_index is not None:
            input_device = self.audio.get_device_info_by_index(mic_index)
        else:
            input_device = self.audio.get_default_input_device_info()
            
        print(f"\n🎤 Recording using: {input_device['name']}")
        print(f"    Sample Rate: {input_device['defaultSampleRate']}Hz")
        print(f"    Max Input Channels: {input_device['maxInputChannels']}")
        
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

        print("Stopping recording...")
        self.cartesia.generate_and_play("thinking...")
        
        # Process collected transcript with LLM before cleanup
        if self.collected_transcript:
            try:
                full_transcript = " ".join(self.collected_transcript)
                print(f"📝 Processing full transcript: {full_transcript}")
                
                # Instead of run_until_complete, schedule on the same loop that is already running
                fut = asyncio.run_coroutine_threadsafe(process_prompt(full_transcript), self.loop)
                response = fut.result()  # Wait for the LLM result
                
                print(f"🤖 LLM Response: {response}")
                
                # Only copy LLM response to clipboard, without pasting
                pyperclip.copy(response)
                self.cartesia.generate_and_play("added to your clipboard")
                
                # Commented out automatic pasting
                # controller = keyboard.Controller()
                # controller.press(keyboard.Key.cmd)
                # controller.press('v')
                # time.sleep(0.1)
                # controller.release('v')
                # controller.release(keyboard.Key.cmd)
                
                
            except Exception as e:
                print(f"❌ Error processing with LLM: {e}")
        
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

def main():
    # Check if running from shortcut
    if len(sys.argv) > 1 and sys.argv[1] == "--from-shortcut":
        print("Running from keyboard shortcut")
    
    if not check_permissions():
        print("Please grant the required permissions and try again")
        return

    transcriber = SpeechTranscriber()
    field_transcriber = FieldTranscriber()
    
    # Create GUI
    gui = SpritelyGUI(transcriber, field_transcriber)
    
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
                    if not transcriber.is_recording:
                        transcriber.start_recording()
                        gui.update_status("AI Transcription Active", True)
                    else:
                        transcriber.stop_recording()
                        gui.update_status("Ready", False)
                elif is_l:
                    if not field_transcriber.is_recording:
                        field_transcriber.start_recording()
                        gui.update_status("Field Transcription Active", True)
                    else:
                        field_transcriber.stop_recording()
                        gui.update_status("Ready", False)
            elif key == keyboard.Key.esc:
                transcriber.stop_recording()
                field_transcriber.stop_recording()
                gui.update_status("Ready", False)
                return False
        except Exception as e:
            print(f"Error handling key press: {e}")
            gui.update_status(f"Error: {str(e)}")

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

    # Track pressed keys
    pressed_keys = set()
    
    # Start keyboard listener in a separate thread
    listener = keyboard.Listener(on_press=on_press_track, on_release=on_release)
    listener.start()
    
    # Start GUI main loop
    gui.run()

if __name__ == "__main__":
    main()