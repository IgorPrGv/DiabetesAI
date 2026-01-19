#!/bin/bash
# Setup script for CrewAI RAG Project


if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip

pip install -r requirements.txt


if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your OPENAI_API_KEY"
else
    echo "✅ .env file already exists"
fi


