import os
import subprocess
import time
from pathlib import Path

# Change working directory to project root
ROOT_DIR = Path(__file__).parent.parent
os.chdir(ROOT_DIR)

def setup_colab():
    print("🪄 Setting up environment for Google Colab...")
    
    # 1. Install dependencies
    print("📦 Installing requirements...")
    subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)
    subprocess.run(["pip", "install", "pyarrow"], check=True) # Often needed for streamlit in Colab
    
    # 2. Check for .env
    if not os.path.exists(".env"):
        print("📝 Creating .env from .env.example...")
        if os.path.exists(".env.example"):
            with open(".env.example", "r") as f:
                content = f.read()
            with open(".env", "r") as f:
                # You might want to prompt for keys or use default placeholder
                pass
    
    # 3. Start Streamlit and Localtunnel
    print("\n🚀 Starting Streamlit...")
    # Start streamlit in background
    streamlit_proc = subprocess.Popen(["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"])
    
    print("\n🌐 Generating Public URL via Localtunnel...")
    print("Note: If it asks for an IP, check the 'Endpoint' in the Colab output.")
    
    # Start localtunnel
    os.system("npx localtunnel --port 8501")

if __name__ == "__main__":
    try:
        setup_colab()
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
