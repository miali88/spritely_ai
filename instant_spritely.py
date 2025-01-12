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
from invoke_llm import process_prompt
from utils.logging_config import setup_logger
from user_settings import settings, save_settings
from transcribe_field import SpeechTranscriber as FieldTranscriber

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
                print(f"📢 Sending {len(data)} bytes of audio data")
                self.dg_connection.send(data)

        self.audio_thread = threading.Thread(target=capture_audio)
        self.audio_thread.start()
        print("Recording started!")

    def stop_recording(self):
        if not self.is_recording:
            return

        print("Stopping recording...")
        
        # Process collected transcript with LLM before cleanup
        if self.collected_transcript:
            try:
                full_transcript = " ".join(self.collected_transcript)
                print(f"📝 Processing full transcript: {full_transcript}")
                
                # Instead of run_until_complete, schedule on the same loop that is already running
                fut = asyncio.run_coroutine_threadsafe(process_prompt(full_transcript), self.loop)
                response = fut.result()  # Wait for the LLM result
                
                print(f"🤖 LLM Response: {response}")
                
                # Copy LLM response to clipboard and paste
                pyperclip.copy(response)
                controller = keyboard.Controller()
                controller.press(keyboard.Key.cmd)
                controller.press('v')
                time.sleep(0.1)
                controller.release('v')
                controller.release(keyboard.Key.cmd)
                
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

def open_accessibility_settings():
    # Opens directly to Accessibility settings
    subprocess.run(['open', 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'])
    print("Please enable accessibility permissions for your application")

def select_microphone():
    """Allow user to select microphone and save preference"""
    audio = pyaudio.PyAudio()
    
    # Get all input devices
    input_devices = []
    print("\n🎤 Available Input Devices:")
    for i in range(audio.get_device_count()):
        dev_info = audio.get_device_info_by_index(i)
        if dev_info['maxInputChannels'] > 0:  # Only show input devices
            input_devices.append((i, dev_info))
            print(f"{len(input_devices)}. {dev_info['name']}")
            print(f"    Channels: {dev_info['maxInputChannels']}")
            print(f"    Sample Rate: {dev_info['defaultSampleRate']}")
    
    # Get default device info
    default_device = audio.get_default_input_device_info()
    print(f"\n🎯 Default Device: {default_device['name']}")
    
    # Show current setting if exists
    if settings['microphone_index'] is not None:
        try:
            current_device = audio.get_device_info_by_index(settings['microphone_index'])
            print(f"📌 Current Setting: {current_device['name']}")
        except:
            print("⚠️ Previously saved device not found")
    
    # Get user selection
    while True:
        choice = input("\nSelect microphone (0 for default, or number from list above): ")
        if choice.strip() == "0":
            settings['microphone_index'] = None
            break
        try:
            index = int(choice) - 1
            if 0 <= index < len(input_devices):
                settings['microphone_index'] = input_devices[index][0]
                break
            else:
                print("❌ Invalid selection. Please try again.")
        except ValueError:
            print("❌ Please enter a number.")
    
    # Save selection
    save_settings()
    audio.terminate()
    return settings['microphone_index']

def check_permissions():
    logger.info("Checking permissions...")
    # Check microphone
    try:
        audio = pyaudio.PyAudio()
        
        # Allow user to select microphone
        mic_index = select_microphone()
        
        # Test selected microphone
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=mic_index,
            frames_per_buffer=CHUNK
        )
        stream.stop_stream()
        stream.close()
        audio.terminate()
        print("✅ Microphone permission granted")
    except Exception as e:
        print("❌ Microphone permission error:", e)
        return False
    
    # Check Deepgram API key
    if not os.getenv('DEEPGRAM_API_KEY'):
        print("❌ Deepgram API key not found in .env file")
        return False
    print("✅ Deepgram API key found")

    # Check accessibility (will raise exception if not granted)
    try:
        with keyboard.Listener(on_press=lambda k: None) as listener:
            listener.stop()
        print("✅ Accessibility permission granted")
    except Exception as e:
        print("❌ Accessibility permission error:", e)
        print("Please enable accessibility permissions for your terminal/Python")
        open_accessibility_settings()
        return False

    return True

def main():
    # Check if running from shortcut
    if len(sys.argv) > 1 and sys.argv[1] == "--from-shortcut":
        print("Running from keyboard shortcut")
    
    # Check if we have accessibility permissions
    try:
        with keyboard.Listener(on_press=lambda k: None) as listener:
            listener.stop()
    except Exception as e:
        print("Accessibility permissions not granted.")
        open_accessibility_settings()
        return

    if not check_permissions():
        print("Please grant the required permissions and try again")
        return

    transcriber = SpeechTranscriber()
    field_transcriber = FieldTranscriber()
    
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
                    else:
                        transcriber.stop_recording()
                elif is_l:
                    if not field_transcriber.is_recording:
                        field_transcriber.start_recording()
                    else:
                        field_transcriber.stop_recording()
            elif key == keyboard.Key.esc:
                transcriber.stop_recording()
                field_transcriber.stop_recording()
                return False
        except Exception as e:
            print(f"Error handling key press: {e}")

    def on_press_track(key):
        if isinstance(key, keyboard.KeyCode):
            pressed_keys.add(key.char)
        else:
            pressed_keys.add(key)
        print(f"Key pressed: {key}")
        print(f"Pressed keys: {pressed_keys}")
        on_press(key)

    def on_release(key):
        try:
            if isinstance(key, keyboard.KeyCode):
                pressed_keys.discard(key.char)
            else:
                pressed_keys.discard(key)
        except KeyError:
            pass

    print("Press Cmd+Option+K to start/stop recording")
    print("Press ESC to exit")
    
    # Track pressed keys
    pressed_keys = set()
    
    # Start listening for keyboard events
    with keyboard.Listener(on_press=on_press_track, on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    main()