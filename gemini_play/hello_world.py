#!/usr/bin/env python3
"""
Simple Gemini LLM Hello World Example
Uses Google's Generative AI API to send a basic prompt and get a response.
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Get the Gemini API key from environment
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables")
        print("Please set your Gemini API key in a .env file or environment variable")
        return
    
    # Configure the API
    genai.configure(api_key=api_key)
    
    # List available models first
    print("Available models:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"  - {m.name}")
    
    # Create a model instance (using gemini-2.0-flash which is available)
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # Send a simple hello world prompt
    prompt = "Hello! Please respond with a friendly greeting and tell me what you can help with."
    
    try:
        print("Sending prompt to Gemini...")
        print(f"Prompt: {prompt}")
        print("-" * 50)
        
        # Generate response
        response = model.generate_content(prompt)
        
        print("Gemini Response:")
        print(response.text)
        
    except Exception as e:
        print(f"Error calling Gemini API: {e}")

if __name__ == "__main__":
    main()
