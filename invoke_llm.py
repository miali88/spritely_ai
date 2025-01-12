from pydantic_ai import Agent
from utils.logging_config import setup_logger

# Initialize logger
logger = setup_logger(__name__)

def create_agent():
    """Create and return a configured Agent instance"""
    logger.debug("Creating new Agent instance")
    try:
        agent = Agent(
            'claude-3-5-sonnet-20240620',
            system_prompt="""You are a helpful assistant, you will receive prompts from the user and respond with your final output only. 
            The user will be using a desktop application that takes your output and pastes it into where the user has located the cursor.
            So please ensure your output is formatted correctly for direct pasting into the input field. With NO prefix or preample like "Here is the output:" or "Here is the result:" or anything like that.
            Simply output the result.
            """
        )
        logger.info("Agent created successfully")
        return agent
    except Exception as e:
        logger.error(f"Failed to create agent: {e}", exc_info=True)
        raise

async def process_prompt(prompt: str) -> str:
    """Process a prompt through the LLM and return the response"""
    logger.info(f"Processing prompt: {prompt[:50]}...")
    try:
        agent = create_agent()
        result = await agent.run(prompt)
        logger.debug("Successfully processed prompt")
        return result.data
    except Exception as e:
        logger.error(f"Error processing prompt: {e}", exc_info=True)
        raise

# Only run this if the file is run directly
if __name__ == "__main__":
    result = process_prompt('Where does "hello world" come from?')
    print(result)