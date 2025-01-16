import pyaudio
from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents
import threading
from datetime import datetime
from dotenv import load_dotenv
import json
from typing import Dict
from colorama import init, Fore, Style
from utils.logging_config import setup_logger
from user_settings import settings
import numpy as np
import time

""" this project streams the transcribd audio, with speaker diarization to terminal
TODO:
- add a way to save the transcriptions to a database
- feed chunks to an LLM for analysis, feedback... info...
"""

load_dotenv()

# Initialize logger
logger = setup_logger(__name__)

# Audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 2  
RATE = 44100  # Sample rate
CHUNK = 1024  # Buffer size in frames

class TranscriberApp:
    def __init__(self):
        self.is_recording = False
        self.audio = None
        self.stream = None
        self.dg_connection = None
        self.audio_thread = None
        self.should_stop = None
        self.transcriptions = []
        self.silence_threshold = 500  # Adjust this value based on your needs

    def is_mic_active(self, duration=1):
        """Check if the microphone is already in use by another application."""
        logger.info("Checking microphone availability...")
        
        try:
            temp_audio = pyaudio.PyAudio()
            # Attempt to open the stream - if it fails, the mic is likely in use
            stream = temp_audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=settings['microphone_index'],
                frames_per_buffer=CHUNK
            )
            
            # If we get here, the mic is available
            stream.stop_stream()
            stream.close()
            temp_audio.terminate()
            return False  # Mic is not active/in-use
            
        except OSError as e:
            logger.warning(f"Microphone appears to be in use: {e}")
            if temp_audio:
                temp_audio.terminate()
            return True  # Mic is active/in-use
        except Exception as e:
            logger.error(f"Error checking microphone: {e}")
            if temp_audio:
                temp_audio.terminate()
            raise

    def start_recording(self):
        if self.is_recording:
            logger.info("Recording already in progress")
            return


        logger.info("Starting recording...")
        self.is_recording = True
        
        # Initialize audio and Deepgram
        self.audio = pyaudio.PyAudio()
        
        # Use the same microphone settings as instant_spritely
        mic_index = settings['microphone_index']
        if mic_index is not None:
            input_device = self.audio.get_device_info_by_index(mic_index)
        else:
            input_device = self.audio.get_default_input_device_info()
            
        print(f"\n🎤 Recording using: {input_device['name']}")
        
        deepgram = DeepgramClient()
        self.dg_connection = deepgram.listen.websocket.v("1")

        # Set up Deepgram connection with the same audio settings
        options = LiveOptions(
            model="nova-2",
            encoding="linear16",
            channels=CHANNELS,
            sample_rate=RATE,
            diarize=True
        )
        
        if self.dg_connection.start(options) is False:
            print("Failed to start Deepgram connection")
            return

        # Update stream creation to use selected microphone
        self.stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=settings['microphone_index'],
            frames_per_buffer=CHUNK
        )

        # Add color mapping for speakers
        speaker_colors: Dict[int, str] = {
            0: Fore.CYAN,
            1: Fore.MAGENTA,
            2: Fore.YELLOW,
            3: Fore.GREEN,
            4: Fore.BLUE,
            5: Fore.RED,
        }

        # Add a list to store all transcriptions
        self.transcriptions = []

        # Store instance reference for closure
        app = self
        
        # Update handler definitions to use the stored reference
        def on_message(connection, result):
            try:
                logger.debug("Processing transcription message")
                if result.is_final:
                    transcript_data = {
                        'timestamp': datetime.now().isoformat(),
                        'transcript': result.channel.alternatives[0].transcript,
                        'confidence': result.channel.alternatives[0].confidence,
                        'words': result.channel.alternatives[0].words,
                        'start_time': result.start,
                        'duration': result.duration,
                        'request_id': result.metadata.request_id
                    }
                    
                    # Use app instead of self
                    app.transcriptions.append(transcript_data)
                    
                    # Get speaker information and color
                    words = result.channel.alternatives[0].words
                    if words and hasattr(words[0], 'speaker'):
                        speaker_num = words[0].speaker
                        color = speaker_colors.get(speaker_num, Fore.WHITE)
                        speaker = f"Speaker {speaker_num}"
                    else:
                        color = Fore.WHITE
                        speaker = "Unknown"
                    
                    # Print colored transcription
                    print(f"[{transcript_data['timestamp']}] {color}{speaker}: {transcript_data['transcript']}{Style.RESET_ALL}")
                    
            except Exception as e:
                logger.error(f"Error in transcription callback: {e}", exc_info=True)
                logger.debug(f"Result type: {type(result)}")
                logger.debug(f"Result content: {result}")

        def on_open(connection):
            print("Connected to Deepgram!")

        def on_close(connection, message=None):
            print("Disconnected from Deepgram!")

        def on_error(connection, error):
            print(f"Error from Deepgram: {error}")

        # Register all event handlers
        self.dg_connection.on(LiveTranscriptionEvents.Open, on_open)
        self.dg_connection.on(LiveTranscriptionEvents.Close, on_close)
        self.dg_connection.on(LiveTranscriptionEvents.Error, on_error)
        self.dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

        print("\nRecording... Press Enter to stop.\n")

        # Create a flag for stopping the recording
        self.should_stop = threading.Event()

        # Define audio capture thread
        def capture_audio():
            while not self.should_stop.is_set():
                data = self.stream.read(CHUNK)
                self.dg_connection.send(data)

        # Start the capture thread
        self.audio_thread = threading.Thread(target=capture_audio)
        self.audio_thread.start()

    def stop_recording(self):
        if not self.is_recording:
            return

        logger.info("Stopping recording...")
        self.should_stop.set()
        self.audio_thread.join()
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
        self.dg_connection.finish()
        self.is_recording = False
        
        # Save transcriptions
        self.save_transcriptions()
        print("Recording stopped!")

    def save_transcriptions(self):
        if self.transcriptions:
            # Convert transcriptions to serializable format
            serializable_transcripts = []
            for t in self.transcriptions:
                # Skip empty transcripts
                if not t['transcript'].strip():
                    continue
                    
                # Extract speaker from words if available
                speaker = None
                if t.get('words') and hasattr(t['words'][0], 'speaker'):
                    speaker = t['words'][0].speaker

                # Create clean transcript object
                transcript_obj = {
                    'timestamp': t['timestamp'],
                    'transcript': t['transcript'],
                    'confidence': t['confidence'],
                    'speaker': speaker,
                    'start_time': t['start_time'],
                    'duration': t['duration'],
                    'request_id': t['request_id']
                }
                serializable_transcripts.append(transcript_obj)

            # Save to file only if we have non-empty transcripts
            if serializable_transcripts:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"meetings/json/transcription_{timestamp}.json"
                with open(filename, 'w') as f:
                    json.dump(serializable_transcripts, f, indent=2)
                print(f"Transcriptions saved to {filename}")

# Add main block
if __name__ == "__main__":
    app = TranscriberApp()
    
    while True:
        app.start_recording()
        if app.is_recording:
            break
        time.sleep(1)  # Wait a second before checking again
    
    # Wait for Enter key to stop recording
    input()
    app.stop_recording()