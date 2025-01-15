from utils.logging_config import setup_logger
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from elevenlabs import stream as play_audio
from elevenlabs.client import ElevenLabs
from anthropic import AsyncAnthropic
from tools import tools
import prompts
import pyperclip

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

class ResponseType:
    SPEAK = "speak"
    CLIPBOARD = "clipboard"
    
async def handle_response(response: str, response_type: str):
    """Handle the response based on its type"""
    logger.info(f"📝 Handling response of type: {response_type}")
    
    if response_type == ResponseType.CLIPBOARD:
        pyperclip.copy(response)
        try:
            # Generate and play audio using ElevenLabs
            audio_stream = eleven_labs.generate(
                text="Added to your clipboard",
                voice="OOjDveYEA7KnRY2FRSmX",
                model="eleven_multilingual_v2",
                stream=True
            )
            play_audio(audio_stream)
            logger.info("🔊 Played clipboard notification audio")
        except Exception as e:
            logger.error(f"Failed to play ElevenLabs audio: {e}")
        logger.info("📋 Response copied to clipboard")
    
    return response, response_type

async def tts_process(collected_chunks: list[str]):
    """Process text chunks through ElevenLabs TTS and play audio"""
    logger.info("🔊 Starting audio generation...")
    
    # Debug the input
    logger.debug(f"🎵 TTS Input chunks: {collected_chunks}")
    
    # Create a synchronous generator for ElevenLabs
    def text_stream():
        for chunk in collected_chunks:
            logger.debug(f"🗣️ Streaming chunk: {chunk}")
            yield chunk

    try:
        # Generate and stream audio
        audio_stream = eleven_labs.generate(
            text=text_stream(),
            voice="OOjDveYEA7KnRY2FRSmX",
            model="eleven_multilingual_v2",
            stream=True
        )
        
        logger.debug("🎵 Audio stream generated, starting playback...")
        play_audio(audio_stream)
        logger.info("✅ Audio playback completed")
    except Exception as e:
        logger.error(f"❌ TTS Error: {str(e)}", exc_info=True)
        raise

async def get_response_type(prompt: str, client: AsyncAnthropic) -> str:
    """Determine whether the response should be spoken or copied to clipboard"""
    logger.debug("🎯 Determining response type...")
    try:
        response = await client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
            system=prompts.RESPONSE_DETECTOR_PROMPT
        )
        response_text = response.content[0].text.lower().strip()
        logger.debug(f"🔍 Raw response type text: {response_text}\n")
        
        # Look for [speak] tag in the response
        if 'speak' in response_text:
            return ResponseType.SPEAK
        
        # Fallback to previous detection method
        is_speak = any(word in response_text for word in ['speak', 'speech', 'voice', 'audio'])
        response_type = ResponseType.SPEAK if is_speak else ResponseType.CLIPBOARD
        
        logger.info(f"📋 Response type determined: {response_type}\n")
        return response_type
    except Exception as e:
        logger.error(f"❌ Error in get_response_type: {e}", exc_info=True)
        raise

async def get_llm_stream(prompt: str, client: AsyncAnthropic):
    """Get the LLM response stream from Anthropic"""
    logger.debug("🌐 Creating Anthropic stream...")
    return client.messages.stream(
        model="claude-3-sonnet-20240229",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
        tools=tools,
        system=prompts.MAIN_PROMPT
    )

async def process_prompt(prompt: str):
    """Process a prompt through the LLM and yield response chunks"""
    logger.info(f"🤖 Processing prompt: {prompt[:50]}...")
    try:
        full_response = []
        current_sentence = []
        
        # Run both requests concurrently
        stream = await get_llm_stream(prompt, anthropic_client)
        response_type_task = get_response_type(prompt, anthropic_client)
        
        # Start both tasks concurrently
        logger.debug("🚀 Starting concurrent tasks...")
        async with stream as stream_context:
            response_type = await response_type_task
            print("RESPONSE TYPE TASK: ", response_type)

            logger.info(f"🎭 Processing stream with response type: {response_type}")
            
            async for chunk in stream_context:
                if chunk.type == "content_block_delta":
                    # Check if the delta has content
                    if hasattr(chunk.delta, 'text'):
                        answer_text = chunk.delta.text
                        # logger.debug(f"📝 Received text chunk: {answer_text[:50]}...")
                    elif hasattr(chunk.delta, 'tool_calls'):
                        answer_text = str(chunk.delta.tool_calls)
                        logger.debug(f"🔧 Received tool call: {answer_text[:50]}...")
                    else:
                        logger.debug("⚠️ Received chunk with no recognizable content")
                        continue
                        
                    current_sentence.append(answer_text)
                    full_response.append(answer_text)
                    
                    # If we detect end of sentence and it's a speak response, send to TTS
                    if response_type == ResponseType.SPEAK and any(end in answer_text for end in ['.', '!', '?', '\n']):
                        sentence = "".join(current_sentence)
                        logger.info(f"🗣️ Sending to TTS: {sentence[:50]}...")
                        try:
                            await tts_process([sentence])
                            logger.debug("✅ TTS processing complete for sentence")
                        except Exception as e:
                            logger.error(f"❌ TTS processing failed: {e}", exc_info=True)
                        current_sentence = []
        
        # Process any remaining text for speech
        if current_sentence and response_type == ResponseType.SPEAK:
            sentence = "".join(current_sentence)
            logger.info(f"🗣️ Processing final sentence: {sentence[:50]}...")
            try:
                await tts_process([sentence])
                logger.debug("✅ Final TTS processing complete")
            except Exception as e:
                logger.error(f"❌ Final TTS processing failed: {e}", exc_info=True)
            
        # Return both the complete response and its type
        complete_response = "".join(full_response)
        logger.info(f"✨ Complete response generated ({len(complete_response)} chars)")
        logger.debug(f"📤 Final response: {complete_response[:100]}...")
        
        # Handle the response before returning
        return await handle_response(complete_response, response_type)
    except Exception as e:
        logger.error(f"❌ Error in process_prompt: {e}", exc_info=True)
        raise

# Update the main function to test both LLM and audio streaming
if __name__ == "__main__":
    import asyncio
    
    async def main():
        try:
            logger.info("🚀 Testing LLM response with audio streaming...")
            response, response_type = await process_prompt(
                "How to reverse entropy",
            )
            logger.info(f"Response type: {response_type}")
            logger.info(f"Full response: {response}")
                
        except Exception as e:
            logger.error(f"❌ Test failed: {e}", exc_info=True)
    
    asyncio.run(main())
    