"""
Setup script for Smart Hiring Suite.
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file from .env.example if it doesn't exist."""
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_file.exists() and env_example.exists():
        print("Creating .env file from .env.example...")
        with open(env_example, 'r') as f:
            content = f.read()
        with open(env_file, 'w') as f:
            f.write(content)
        print("✓ .env file created. Please edit it with your API keys.")
    elif env_file.exists():
        print("✓ .env file already exists.")
    else:
        print("⚠ .env.example not found. Creating basic .env file...")
        basic_env = """# OpenAI Configuration
OPENAI_API_KEY=
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Vector Database Selection
VECTOR_DB=chroma
CHROMA_DIR=./chroma

# Database Configuration
DATABASE_URL=sqlite:///./data/smart_hiring.db

# Application Settings
LOG_LEVEL=INFO
"""
        with open(env_file, 'w') as f:
            f.write(basic_env)
        print("✓ Basic .env file created. Please add your API keys.")

def create_directories():
    """Create necessary directories."""
    directories = [
        "data/uploads",
        "data/sample_resumes",
        "data/sample_jobs",
        "chroma"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✓ Directories created.")

def main():
    """Main setup function."""
    print("Setting up Smart Hiring Suite...")
    print()
    
    create_directories()
    create_env_file()
    
    print()
    print("Setup complete!")
    print()
    print("Next steps:")
    print("1. Edit .env file with your API keys (optional for local dev)")
    print("2. Run: python -m utils.load_sample_jobs (to load sample job postings)")
    print("3. Start backend: uvicorn backend.app:app --reload")
    print("4. Start frontend: streamlit run frontend/app.py")

if __name__ == "__main__":
    main()

