from utils.logging_config import setup_logger
import httpx
import json
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from elevenlabs import stream
from elevenlabs.client import ElevenLabs

# Load environment variables from .env file
load_dotenv()
eleven_labs = ElevenLabs()

# Initialize logger
logger = setup_logger(__name__)

class ChatMessage(BaseModel):
    message: str
    agent_id: str
    room_name: str

async def process_prompt(prompt: str):
    """Process a prompt through the LLM and yield response chunks"""
    logger.info(f"Processing prompt: {prompt[:50]}...")
    try:
        chat_message = ChatMessage(
            message=prompt,
            agent_id="7649d9c5-a2b0-4082-805e-262f6b11d7db",
            room_name="dev"
        )
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            base_url = 'http://localhost:8000/api/v1'
            logger.debug(f"Calling API at: {base_url}/chat/")
            
            # Store chunks for TTS
            collected_chunks = []
            
            async with client.stream(
                'POST',
                f"{base_url}/chat/",
                json=chat_message.model_dump()
            ) as response:
                response.raise_for_status()
                
                async for chunk in response.aiter_text():
                    if not chunk.strip():
                        continue
                    
                    if chunk.startswith("data: "):
                        chunk = chunk[6:]
                    
                    try:
                        chunk_data = json.loads(chunk)
                        answer_text = chunk_data["response"]["answer"]
                        collected_chunks.append(answer_text)
                        
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Error processing chunk: {e}")
                        continue

            # Create a synchronous generator for ElevenLabs
            def text_stream():
                for chunk in collected_chunks:
                    yield chunk

            # Generate and stream audio
            audio_stream = eleven_labs.generate(
                text=text_stream(),
                voice="Brian",
                model="eleven_multilingual_v2",
                stream=True
            )
            
            stream(audio_stream)
            
        logger.debug("Successfully processed prompt")
    except Exception as e:
        logger.error(f"Error processing prompt: {e}", exc_info=True)
        raise

# Update the main function to test both LLM and audio streaming
if __name__ == "__main__":
    import asyncio
    
    async def main():
        try:
            logger.info("Testing LLM response with audio streaming...")
            await process_prompt("Tell me a short joke")
                
        except Exception as e:
            logger.error(f"Test failed: {e}", exc_info=True)
    
    asyncio.run(main())
    