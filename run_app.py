import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_dependencies():
    """Check if requirements are installed."""
    print("Checking dependencies...")
    try:
        import streamlit
        import pandas
        import requests
        import bs4
        import dotenv
        import pydantic
        import plotly
        return True
    except ImportError:
        return False

def install_dependencies():
    """Install requirements from requirements.txt."""
    print("Installing missing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def setup_env():
    """Ensure .env exists."""
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            print("Creating .env from .env.example...")
            shutil.copy(".env.example", ".env")
            print("Done. Please update .env with your Gemini API keys if needed.")
        else:
            print("Warning: .env.example not found. Skipping .env creation.")

def main():
    # 1. Setup Environment
    setup_env()
    
    # 2. Check/Install Dependencies
    if not check_dependencies():
        install_dependencies()
    
    # 3. Run Streamlit
    print("\nStarting Pune Auction Intelligence Dashboard...")
    try:
        # Use subprocess.Popen to allow the script to exit or continue
        cmd = [sys.executable, "-m", "streamlit", "run", "app.py"]
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nStopping application...")

if __name__ == "__main__":
    main()
