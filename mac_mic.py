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

load_dotenv()

""" transcribed audio to cursor/input field """

# Audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
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
        self.wake_word_detected = False
        self.last_wake_word_time = None
        self.WAKE_WORD = ["hey sprite","hay sprite"]
        self.END_PHRASE = ["end hey sprite","end hay sprite", "and hey sprite", "and hay sprite"]
        self.llm_enabled = True  # Flag to control LLM processing
        self.collecting_transcript = False
        self.collected_transcript = []

    def message_handler(self, event, result):
        """Synchronous wrapper for the async message handler"""
        asyncio.run_coroutine_threadsafe(self.on_message(event, result), self.loop)

    def handle_wake_word(self, transcript):
        """Handle wake word detection and timing with fuzzy matching"""
        current_time = datetime.now()
        
        # Clean the transcript for comparison
        cleaned_transcript = transcript.lower()
        cleaned_transcript = ''.join(char for char in cleaned_transcript if char.isalnum() or char.isspace())
        
        # Check for end phrase first
        for end_phrase in self.END_PHRASE:
            cleaned_end_phrase = ''.join(char for char in end_phrase.lower() if char.isalnum() or char.isspace())
            if cleaned_end_phrase in cleaned_transcript and self.collecting_transcript:
                print(f"\n🛑 End phrase detected at {current_time.strftime('%H:%M:%S')}!")
                self.on_end_phrase_detected(transcript)
                return
            
        # Check for wake word
        for wake_word in self.WAKE_WORD:
            cleaned_wake_word = ''.join(char for char in wake_word.lower() if char.isalnum() or char.isspace())
            if cleaned_wake_word in cleaned_transcript:
                if (not self.last_wake_word_time or 
                    (current_time - self.last_wake_word_time).seconds > 3):
                    self.wake_word_detected = True
                    self.last_wake_word_time = current_time
                    print(f"\n🎯 Wake word detected at {current_time.strftime('%H:%M:%S')}!")
                    self.on_wake_word_detected(transcript)
                    break

    def on_end_phrase_detected(self, transcript):
        """Process collected transcript and stop recording"""
        print(f"🔚 End phrase triggered! Processing collected transcript...")
        
        if self.llm_enabled and self.collected_transcript:
            try:
                # Join all collected transcripts and clean the end phrase
                full_transcript = " ".join(self.collected_transcript)
                
                # Remove all end phrases from the transcript
                for end_phrase in self.END_PHRASE:
                    full_transcript = full_transcript.replace(end_phrase.lower(), "").strip()
                
                print(f"📝 Collected transcript: {full_transcript}")
                
                # Process with LLM
                response = process_prompt(full_transcript)
                print(f"🤖 LLM Response: {response}")
                
                # Optional: copy response to clipboard
                # pyperclip.copy(response)
            except Exception as e:
                print(f"❌ Error processing with LLM: {e}")
        
        # Reset collection state
        self.collecting_transcript = False
        self.collected_transcript = []
        self.stop_recording()

    def on_wake_word_detected(self, transcript):
        """Start collecting transcript after wake word"""
        print(f"🤖 Wake word triggered! Starting collection...")
        self.collecting_transcript = True
        self.collected_transcript = []
        # Remove all wake words from transcript
        cleaned = transcript.lower()
        for wake_word in self.WAKE_WORD:
            cleaned = cleaned.replace(wake_word.lower(), "")
        cleaned = cleaned.strip()
        if cleaned:
            self.collected_transcript.append(cleaned)
    
    async def on_message(self, event, result):
        logger.debug(f"Received message - Event type: {event}")
        print(f"Result type: {type(result)}")
        try:
            # Create a timestamp for the transcription
            timestamp = datetime.now().isoformat()
            
            print("\n=== Transcription Debug ===")
            print(f"[{timestamp}] Raw result: {result}")
            
            if hasattr(result, 'is_final'):  # Add safety check
                if result.is_final:
                    transcript = result.channel.alternatives[0].transcript
                    # Add space after the transcript
                    transcript = transcript.strip() + " "
                    confidence = result.channel.alternatives[0].confidence
                    
                    # Handle wake word and end phrase detection
                    self.handle_wake_word(transcript)
                    
                    # If we're collecting and it's not a wake word or end phrase, add to collection
                    if self.collecting_transcript:
                        cleaned = transcript.strip()
                        if cleaned:
                            self.collected_transcript.append(cleaned)
                            print(f"📝 Adding to transcript: {cleaned}")
                    
                    # Print detailed transcription info
                    print(f"\n🎤 Transcription Details:")
                    print(f"📝 Transcript: {transcript}")
                    print(f"✨ Confidence: {confidence:.2f}")
                    
                    # Filter out wake words one by one
                    filtered_transcript = transcript.lower()
                    for wake_word in self.WAKE_WORD:
                        filtered_transcript = filtered_transcript.replace(wake_word.lower(), "")
                    filtered_transcript = filtered_transcript.strip() + " "

                    if filtered_transcript.strip():
                        self.current_transcription = filtered_transcript
                        print(f"\n📋 Actions:")
                        print(f"1. Copying to clipboard: {filtered_transcript}")
                        # Copy filtered transcript to clipboard
                        pyperclip.copy(filtered_transcript)
                        time.sleep(0.1)
                        
                        print("2. ⌨️ Simulating paste command...")
                        # Create controller without context manager
                        controller = keyboard.Controller()
                        controller.press(keyboard.Key.cmd)
                        controller.press('v')
                        time.sleep(0.1)
                        controller.release('v')
                        controller.release(keyboard.Key.cmd)
                        print("✅ Paste command completed")
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
        
        # Initialize audio and Deepgram
        self.audio = pyaudio.PyAudio()
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

        # Start audio stream
        self.stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
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

def check_permissions():
    logger.info("Checking permissions...")
    # Check microphone
    try:
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
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
    
    def on_press(key):
        try:
            # Convert the key to string for comparison
            key_str = str(key).replace("'", "")
            print(f"Debug - Key string: {key_str}, Pressed keys: {pressed_keys}")  # Debug line
            
            # Check for both left and right alt keys
            alt_pressed = any(k in pressed_keys for k in [keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r])
            cmd_pressed = keyboard.Key.cmd in pressed_keys
            
            # Check if the key is 'k' (either direct or as part of a combination)
            is_k = key_str.lower() == 'k' or '˚' in pressed_keys
            
            if cmd_pressed and alt_pressed and (is_k or key_str == '˚'):
                if not transcriber.is_recording:
                    transcriber.start_recording()
                else:
                    transcriber.stop_recording()
            elif key == keyboard.Key.esc:
                transcriber.stop_recording()
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