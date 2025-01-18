import os
import logging
from dotenv import load_dotenv

from anthropic import Anthropic

# Set up logging configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler with formatting
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

load_dotenv()

anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

sys_prompt = """
Your job is to review the user's notes, the transcript of a meeting, to then summarize the meeting.

Review the topic and notes to understand the context of the meeting and topics discussed. 

The summary will be structured as a list of bullet points, with headings separating the topics.

Attempt to arrange the meeting in a chronological order. 

Your bullet points will include the user's notes as far as possible.

Prioritize dates, monies, names, and other important information.
"""


def ai_summary(meeting_transcript=str, user_notes= str | None): 
    logger.info("Starting AI summary generation")
    
    if not meeting_transcript:
        logger.error("No meeting transcript provided")
        return None
        
    prompt = f"""
    <instructions>
    Review the meeting_transcript, and the user_notes
    User notes included in the summary must be highlighted with a "* *" syntax to show that this is the user's notes.
    </instructions>
    <meeting_transcript>
    {meeting_transcript}
    </meeting_transcript>
    """   
    
    if user_notes:
        logger.debug("Adding user notes to prompt")
        prompt += f"""
        <user_notes>
        {user_notes}
        </user_notes>
        """
    
    try:
        logger.debug("Sending request to Claude API")
        message = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=8192,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": prompt
            }],
            system=sys_prompt
        )
        logger.info("Successfully received response from Claude API")
        print(message.content[0].text)
        return message.content[0].text
        
    except Exception as e:
        logger.error(f"Error during API call: {str(e)}")
        raise

