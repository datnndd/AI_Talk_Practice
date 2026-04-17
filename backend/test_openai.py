import asyncio
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

async def main():
    client = AsyncOpenAI(
        api_key=os.environ.get("LLM_API_KEY"),
        base_url=os.environ.get("LLM_BASE_URL"),
    )
    
    print("Testing connection with AsyncOpenAI library to 9router...")
    
    try:
        stream = await client.chat.completions.create(
            model=os.environ.get("LLM_MODEL", "ai-talk"),
            messages=[{"role": "user", "content": "Hello! How are you?"}],
            stream=True,
            temperature=0.7,
            max_tokens=100
        )
        
        print("Stream started successfully.")
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                print(f"Content: {chunk.choices[0].delta.content}", flush=True)
                
    except Exception as e:
        print(f"Exception using AsyncOpenAI: {e}")

if __name__ == "__main__":
    asyncio.run(main())
