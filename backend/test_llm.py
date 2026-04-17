import asyncio
import httpx
import sys
import os

# Add backend directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

async def main():
    print("--- 9router LLM Connection Test ---")
    
    api_key = settings.llm_api_key
    if api_key:
        masked_key = f"{api_key[:5]}...{api_key[-4:]}" if len(api_key) > 10 else "***"
    else:
        masked_key = "None"
        
    print(f"Provider: {settings.llm_provider}")
    print(f"Model: {settings.llm_model}")
    print(f"Base URL: {settings.llm_base_url}")
    print(f"API Key: {masked_key}")
    print("-" * 35)
    
    url = f"{settings.llm_base_url}/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    print(f"\n[1] Testing /models endpoint (GET {url})...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            print(f"Status Code: {resp.status_code}")
            if resp.status_code == 200:
                print("Success! The API is reachable and accepting your token.")
                models_data = resp.json()
                if "data" in models_data:
                    available_models = [m.get("id") for m in models_data["data"]]
                    print(f"Available models (first 5): {available_models[:5]}")
                    if settings.llm_model in available_models:
                        print(f"OK: Your selected model '{settings.llm_model}' is available.")
                    else:
                        print(f"WARNING: Your selected model '{settings.llm_model}' is NOT in the available models list.")
            else:
                print(f"Failed! API returned: {resp.text[:500]}")
    except Exception as e:
        print(f"Connection Error: {e}")

    chat_url = f"{settings.llm_base_url}/chat/completions"
    print(f"\n[2] Testing /chat/completions endpoint (POST {chat_url})...")
    payload = {
        "model": settings.llm_model,
        "messages": [{"role": "user", "content": "Hello, this is a test connection. Reply with exactly 'OK'."}],
        "max_tokens": 10
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(chat_url, headers=headers, json=payload)
            print(f"Status Code: {resp.status_code}")
            
            if resp.status_code == 200:
                print("Parsing stream responses:")
                lines = resp.text.split('\n')
                for line in lines[:20]: # print up to 20 lines
                    if line.startswith("data: "):
                        print(f" - {line[:100]}...")
                print("Success! Handled streaming response without JSON error.")
            else:
                print(f"Failed HTTP Status! API returned: {resp.text[:500]}")
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
