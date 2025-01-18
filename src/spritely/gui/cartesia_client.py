from cartesia import Cartesia
import os
import wave
import pyaudio
from dotenv import load_dotenv
import os 
import logging

logger = logging.getLogger(__name__)

load_dotenv()

class CartesiaClient:
    def __init__(self):
        logger.info("Initializing CartesiaClient")
        self.client = Cartesia(api_key=os.environ.get("CARTESIA_API_KEY"))
        self.audio = pyaudio.PyAudio()

    def generate_and_play(self, text):
        logger.info(f"Generating and playing audio: '{text}'")
        # Generate audio bytes
        try:
            audio_data = self.client.tts.bytes(
                model_id="sonic-english",
                transcript=text,
                voice_id="729651dc-c6c3-4ee5-97fa-350da1f88600",  # Barbershop Man
                output_format={
                    "container": "wav",
                    "encoding": "pcm_s16le",
                    "sample_rate": 44100,
                },
            )
            logger.debug("Audio generated successfully")

            # Save temporary WAV file
            temp_file = "temp_audio.wav"
            with open(temp_file, "wb") as f:
                f.write(audio_data)
            logger.debug("Temporary audio file saved")

            # Play the audio with explicit format
            with wave.open(temp_file, 'rb') as wf:
                stream = self.audio.open(
                    format=pyaudio.paInt16,
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True
                )
                logger.debug("Audio stream opened")

                data = wf.readframes(1024)
                while data:
                    stream.write(data)
                    data = wf.readframes(1024)

                stream.stop_stream()
                stream.close()
                logger.debug("Audio playback completed")

            # Clean up temporary file
            os.remove(temp_file)
            logger.debug("Temporary audio file removed")

        except Exception as e:
            logger.error(f"Error in generate_and_play: {str(e)}")
            raise 