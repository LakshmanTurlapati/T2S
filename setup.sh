#!/bin/bash

# Text2SQL for Event Management - Setup Script 🚀
# This script will set up everything you need to run the Text2SQL application

echo "🌟 Setting up Text2SQL for Event Management 🌟"
echo "=============================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker and try again."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose and try again."
    exit 1
fi

echo "✅ Prerequisites check passed!"

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install requirements
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists, if not create it
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️ Please edit the .env file with your database connection details if needed."
else
    echo "✅ .env file already exists."
fi

# Start the database
echo "🐘 Starting PostgreSQL database..."
docker-compose up -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Generate data
echo "🔄 Generating sample data..."
python data.py

echo "🎉 Setup complete! 🎉"
echo "=============================================="
echo "To run the application, use: python main.py"
echo "Enjoy converting natural language to SQL queries! ✨" 