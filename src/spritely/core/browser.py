from browser_use import Agent, Browser, BrowserConfig
from langchain_openai import ChatOpenAI
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

# Configure the browser to connect to your Chrome instance
browser = Browser(
    config=BrowserConfig(
        # Specify the path to your Chrome executable
        chrome_instance_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',  # macOS path
        # For Windows, typically: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
        # For Linux, typically: '/usr/bin/google-chrome'
    )
)

async def execute_browser_task(task: str) -> str:
    agent = Agent(
        task=task,
        llm=ChatOpenAI(model="gpt-4o"),  # Fixed typo in model name
        browser=browser,
    )
    result = await agent.run()
    await browser.close()
    return result

async def main():
    result = await execute_browser_task(
        """go onto this url, click the first lead's linkedin url, then send a message draft message to 
           them saying "hello there". DO NOT SEND THE MESSAGE.
           url: https://small-limit-60e.notion.site/Flowon-AI-Leads-18b53e390487806b918ffcc22e543600?pvs=74
        """
    )
    print(result)
    input('Press Enter to close the browser...')

if __name__ == '__main__':
    asyncio.run(main())