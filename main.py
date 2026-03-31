import os
import sys
import uvicorn

print("Booting up LeanX Coach Server...")

try:
    # 1. The correct import path
    from google.adk.cli.fast_api import get_fast_api_app
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. The required 'web=True' argument
    app = get_fast_api_app(agents_dir=current_dir, web=True)
    print("Agent loaded successfully via ADK FastAPI wrapper!")
    
except Exception as e:
    print(f"CRITICAL BOOT ERROR: {str(e)}")
    sys.exit(1)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting Uvicorn on port {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port)