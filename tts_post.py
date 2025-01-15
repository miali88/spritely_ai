import requests
import logging
import os
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def text_to_speech(
    text: str,
    voice_id: str,
    api_key: str,
    model_id: Optional[str] = None
) -> Optional[bytes]:
    """
    Convert text to speech using ElevenLabs API
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8
        }
    }

    logger.info(f"Sending TTS request for text: {text[:50]}...")
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        logger.info("Successfully received audio response")
        return response.content
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during API request: {str(e)}")
        return None

if __name__ == "__main__":
    # Get API key from environment variable
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        logger.error("No API key found in environment variables")
        exit(1)
    
    # Example voice ID (replace with your actual voice ID)
    voice_id = "OOjDveYEA7KnRY2FRSmX"
    
    # Example text
    text = "Hello world! This is a test of the ElevenLabs text to speech API."
    
    logger.info("Starting text to speech conversion")
    audio_data = text_to_speech(text, voice_id, api_key)
    
    if audio_data:
        output_file = "output.mp3"
        # Save the audio file
        with open(output_file, "wb") as f:
            f.write(audio_data)
        logger.info(f"Audio file saved as {output_file}")
        
        # Play the audio file using pygame
        try:
            import pygame
            logger.info("Playing audio file...")
            pygame.mixer.init()
            pygame.mixer.music.load(output_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():  # wait for music to finish playing
                pygame.time.Clock().tick(10)
            logger.info("Finished playing audio file")
        except ImportError:
            logger.error("Please install pygame package: pip install pygame")
        except Exception as e:
            logger.error(f"Error playing audio file: {str(e)}")
    else:
        logger.error("Failed to generate audio")
