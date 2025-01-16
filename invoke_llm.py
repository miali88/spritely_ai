from utils.logging_config import setup_logger
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from elevenlabs import stream as play_audio
from elevenlabs.client import ElevenLabs
from anthropic import Anthropic
from tools import tools
import prompts
import pyperclip
from typing import Literal
from groq import Groq

load_dotenv()

eleven_labs = ElevenLabs()
anthropic_client = Anthropic()
groq_client = Groq()

# Initialize logger
logger = setup_logger(__name__, log_level="DEBUG", use_color=True)

# Add near the top of the file with other globals
current_audio_stream = None

class ChatMessage(BaseModel):
    message: str
    agent_id: str
    room_name: str

class ResponseType:
    SPEAK: Literal["speak"] = "speak"
    CLIPBOARD: Literal["clipboard"] = "clipboard"
    STORE: Literal["store"] = "store"
    FIELD: Literal["field"] = "field"

ResponseTypeStr = Literal["speak", "clipboard", "store", "field"]

async def save_to_clipboard(prompt: str) -> str:
    """Save LLM response to clipboard and play notification.
    
    Args:
        prompt: Input prompt for LLM
        
    Returns:
        str: Combined response text
    """
    logger.debug("📋 Starting clipboard save operation...")
    
    # Collect full response
    response_text = "".join([chunk for chunk in llm_clipboard(prompt)])
    pyperclip.copy(response_text)
    
    try:
        # Generate and play audio using ElevenLabs
        audio_stream = eleven_labs.generate(
            text="Added to your clipboard, let me know what's next",
            voice="OOjDveYEA7KnRY2FRSmX",
            model="eleven_multilingual_v2",
            stream=True
        )
        play_audio(audio_stream)
        logger.info("🔊 Played clipboard notification audio")
        logger.debug("🔊 Generated clipboard notification audio")
    except Exception as e:
        logger.error(f"🔇 Audio notification failed: {e}", exc_info=True)
    
    return response_text


def llm_clipboard(prompt: str):
    message = anthropic_client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1024,
        temperature=0.4,
        messages=[{
            "role": "user",
            "content": prompt
        }],
        stream=True,
        system=prompts.CLIPBOARD_PROMPT
    )
    
    for chunk in message:
        if chunk.type == "content_block_delta":
            logger.debug(f"📝 Received chunk: {chunk.delta.text[:20]}...")
            yield chunk.delta.text

def llm_speak(prompt: str):
    message = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        temperature=0.4,
        messages=[{
            "role": "user",
            "content": prompt
        }],
        stream=True,
        system=prompts.SPEAK_PROMPT
    )
    for chunk in message:
        if chunk.type == "content_block_delta":
            logger.debug(f"📝 Received chunk: {chunk.delta.text[:20]}...")
            yield chunk.delta.text

def tts_service(prompt: str):
    audio_stream = eleven_labs.generate(
        text=llm_speak(prompt),
        voice="OOjDveYEA7KnRY2FRSmX",
        model="eleven_multilingual_v2",
        stream=True
    )
    logger.debug("🔊 Generated audio stream, starting playback...")
    play_audio(audio_stream)
    logger.info("✅ Completed audio playback")

async def get_response_type(prompt: str, client: Anthropic) -> str:
    """Determine whether the response should be spoken or copied to clipboard"""
    logger.debug("🎯 Determining response type...")
    try:

        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": prompts.RESPONSE_DETECTOR_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama3-70b-8192",
        )

        response_text = chat_completion.choices[0].message.content
    
        logger.debug(f"🔍 Raw response type text: {response_text}\n")
        
        # Look for [speak] tag in the response
        if 'speak' in response_text:
            return ResponseType.SPEAK
        elif 'clipboard' in response_text:
            return ResponseType.CLIPBOARD
        
        # Fallback to previous detection method
        is_speak = any(word in response_text for word in ['speak', 'speech', 'voice', 'audio'])
        response_type = ResponseType.SPEAK if is_speak else ResponseType.CLIPBOARD
        
        logger.info(f"📋 Response type determined: {response_type}\n")
        return response_type
    except Exception as e:
        logger.error(f"❌ Error in get_response_type: {e}", exc_info=True)
        raise

async def process_prompt(prompt: str) -> tuple[str, ResponseTypeStr]:
    """Main prompt processing pipeline.
    
    Args:
        prompt: User input prompt
        
    Returns:
        tuple[str, ResponseTypeStr]: The response text and the response type
    """
    logger.info(f"🎯 Processing prompt: {prompt[:50]}...")
    
    try:
        response_type = await get_response_type(prompt, anthropic_client)
        logger.info(f"📋 Determined response type: {response_type}")
        
        if response_type == ResponseType.SPEAK:
            await tts_service(prompt)
            return "", response_type  # Return empty string since audio was played
        elif response_type == ResponseType.CLIPBOARD:
            response_text = await save_to_clipboard(prompt)
            return response_text, response_type
        elif response_type == ResponseType.STORE:
            return "", response_type
        
            
    except Exception as e:
        logger.error(f"❌ Processing failed: {e}", exc_info=True)
        raise

# Update the main function to test both LLM and audio streaming
if __name__ == "__main__":
    import asyncio
    
    async def main():
        try:
            logger.info("🚀 Testing LLM response with audio streaming...")
            response, response_type = await process_prompt(
                "tell me a joke",
            )
            logger.info(f"Response type: {response_type}")
            logger.info(f"Full response: {response}")
                
        except Exception as e:
            logger.error(f"❌ Test failed: {e}", exc_info=True)
    
    asyncio.run(main())
    