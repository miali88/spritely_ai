from utils.logging_config import setup_logger
import httpx
import json
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from elevenlabs import stream as play_audio
from elevenlabs.client import ElevenLabs
import colorlog
from anthropic import AsyncAnthropic

# Load environment variables from .env file
load_dotenv()
eleven_labs = ElevenLabs()
anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Initialize logger
logger = setup_logger(__name__, log_level="DEBUG", use_color=True)

class ChatMessage(BaseModel):
    message: str
    agent_id: str
    room_name: str

async def process_prompt(prompt: str):
    """Process a prompt through the LLM and yield response chunks"""
    logger.info(f"🤖 Processing prompt: {prompt[:50]}...")
    try:
        logger.debug("🌐 Calling Anthropic API...")
        
        # Store chunks for TTS
        collected_chunks = []
        
        async with anthropic_client.messages.stream(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            async for chunk in stream:
                if chunk.type == "content_block_delta":
                    answer_text = chunk.delta.text
                    collected_chunks.append(answer_text)

        # Create a synchronous generator for ElevenLabs
        def text_stream():
            for chunk in collected_chunks:
                yield chunk

        logger.info("🔊 Starting audio generation...")
        # Generate and stream audio
        audio_stream = eleven_labs.generate(
            text=text_stream(),
            voice="Brian",
            model="eleven_multilingual_v2",
            stream=True
        )
        
        logger.debug("🎵 Streaming audio...")
        play_audio(audio_stream)
        
        logger.info("✅ Successfully processed prompt")
    except Exception as e:
        logger.error(f"❌ Error processing prompt: {e}", exc_info=True)
        raise

# Update the main function to test both LLM and audio streaming
if __name__ == "__main__":
    import asyncio
    
    async def main():
        try:
            logger.info("🚀 Testing LLM response with audio streaming...")
            await process_prompt("Tell me a short joke")
                
        except Exception as e:
            logger.error(f"❌ Test failed: {e}", exc_info=True)
    
    asyncio.run(main())
    