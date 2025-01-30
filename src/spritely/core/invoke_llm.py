from pydantic import BaseModel
from dotenv import load_dotenv
import os
from elevenlabs import stream as play_audio
from elevenlabs.client import ElevenLabs
from anthropic import Anthropic
import prompts
import pyperclip
from typing import Literal, List, Dict
from groq import Groq
from datetime import datetime

from src.spritely.utils.logging import setup_logging
from src.spritely.core.tools import tools
from src.spritely.core.browser import execute_browser_task

load_dotenv()

eleven_labs_api_key = os.getenv("ELEVENLABS_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")

eleven_labs = ElevenLabs(api_key=eleven_labs_api_key)
anthropic_client = Anthropic(api_key=anthropic_api_key)
groq_client = Groq(api_key=groq_api_key)

# Initialize logger
logger = setup_logging(log_level="DEBUG", use_color=True)

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

class ConversationMemory:
    def __init__(self, max_history: int = 10):
        self.history: List[Dict] = []
        self.max_history = max_history
    
    def add_exchange(self, user_input: str, response: str, response_type: str):
        """Add a conversation exchange to memory"""
        exchange = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "response": response,
            "response_type": response_type
        }
        self.history.append(exchange)
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    def get_context(self) -> str:
        """Get formatted conversation history for context"""
        context = []
        for exchange in self.history:
            context.append(f"[User]: {exchange['user_input']}")
            context.append(f"[Assistant ({exchange['response_type']})]: {exchange['response']}")
        return "\n".join(context)

# Initialize conversation memory
conversation_memory = ConversationMemory()

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
        model="claude-3-5-sonnet-20241022",
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
        model="claude-3-5-sonnet-20241022",
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

async def tts_service(prompt: str):
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
    logger.info(f"🎯 Processing prompt: {prompt[:50]}...")
    
    try:
        # Check for browser-related keywords
        if any(keyword in prompt.lower() for keyword in ['use the browser', 'use the internet']):
            logger.info("🌐 Browser action detected, invoking browser tool...")
            try:
                result = await execute_browser_task(prompt)
                response_text = f"Browser task completed. Result: {result}"
                response_type = ResponseType.CLIPBOARD
                conversation_memory.add_exchange(prompt, response_text, response_type)
                return response_text, response_type
            except Exception as e:
                logger.error(f"❌ Browser task failed: {e}", exc_info=True)
                raise

        # Get conversation history context
        context = conversation_memory.get_context()
        
        # Add thinking tags and context to the prompt
        enhanced_prompt = f"""<conversation_history>
{context}
</conversation_history>

<current_request>
{prompt}
</current_request>

<thinking>Please consider the conversation history above when formulating your response.</thinking>"""

        response_type = await get_response_type(enhanced_prompt, anthropic_client)
        logger.info(f"📋 Determined response type: {response_type}")
        
        response_text = ""
        if response_type == ResponseType.SPEAK:
            await tts_service(enhanced_prompt)
        elif response_type == ResponseType.CLIPBOARD:
            response_text = await save_to_clipboard(enhanced_prompt)
        elif response_type == ResponseType.STORE:
            pass
            
        # Store the exchange in memory
        conversation_memory.add_exchange(prompt, response_text, response_type)
        
        return response_text, response_type
            
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
    