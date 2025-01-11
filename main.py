import pyaudio
from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents
import threading
from datetime import datetime
from dotenv import load_dotenv
import json
from typing import Dict
from colorama import init, Fore, Style
from utils.logging_config import setup_logger

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
CHANNELS = 1  # Mono
RATE = 44100  # Sample rate
CHUNK = 1024  # Buffer size in frames

def main():
    logger.info("Starting main application")
    try:
        # Initialize colorama for Windows compatibility
        init()

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
        transcriptions = []

        # Initialize PyAudio and Deepgram
        audio = pyaudio.PyAudio()
        deepgram = DeepgramClient()
        dg_connection = deepgram.listen.websocket.v("1")

        # Add connection status handlers with correct signatures
        def on_open(self, connection):
            print("Connected to Deepgram!")

        def on_close(self, connection):
            print("Disconnected from Deepgram!")

        def on_error(self, error):
            print(f"Error from Deepgram: {error}")

        def on_message(self, result):
            try:
                logger.debug("Processing transcription message")
                # Check if the result is final
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
                    
                    # Store the transcription
                    transcriptions.append(transcript_data)
                    
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

        # Register all event handlers
        dg_connection.on(LiveTranscriptionEvents.Open, on_open)
        dg_connection.on(LiveTranscriptionEvents.Close, on_close)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)
        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

        # Start Deepgram connection with more detailed error handling
        options = LiveOptions(
            model="nova-2",
            encoding="linear16",
            channels=CHANNELS,
            sample_rate=RATE,
            diarize=True  # Enable speaker diarization
        )
        
        if dg_connection.start(options) is False:
            print("Failed to start Deepgram connection")
            return

        # Start audio stream
        stream = audio.open(format=FORMAT,
                          channels=CHANNELS,
                          rate=RATE,
                          input=True,
                          frames_per_buffer=CHUNK)

        print("\nRecording... Press Enter to stop.\n")

        # Create a flag for stopping the recording
        should_stop = threading.Event()

        # Define audio capture thread
        def capture_audio():
            while not should_stop.is_set():
                data = stream.read(CHUNK)
                dg_connection.send(data)

        # Start the capture thread
        audio_thread = threading.Thread(target=capture_audio)
        audio_thread.start()

        # Modify the cleanup section to save transcriptions
        def save_transcriptions():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transcription_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(transcriptions, f, indent=2)
            print(f"Transcriptions saved to {filename}")

        # Wait for Enter key
        input("")
        should_stop.set()

        # Clean up
        audio_thread.join()
        stream.stop_stream()
        stream.close()
        audio.terminate()
        dg_connection.finish()
        
        # Save transcriptions before exiting
        save_transcriptions()
        print("Finished recording")

    except Exception as e:
        logger.error(f"Main application error: {e}", exc_info=True)
        return

if __name__ == "__main__":
    main()