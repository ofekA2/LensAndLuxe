import os
from openai import OpenAI
import requests
import base64


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def analyze_clothing_image(image_path):
    """
    Analyze clothing image using OpenAI's vision API
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        str: Description of clothing type and colors
    """
    
    # Get API key from environment variable
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    # Encode the image
    try:
        base64_image = encode_image(image_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "i want you to return 2 things in 2 different lines: first line is going to be the type of clothing in the image. you will return it by the subcategories ahead: for dresses, return either long dress or short dress. for skirts, return either long skirt or short skirt. for pants, return either pants or shorts. for upperwear, return either button-up shirt, hoodie, jacket or oversized t-shirt. second line is going to be the color of the clothing in the image. return 3 colors maximum if the clothing has a few colors (the main ones)."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        response_data = response.json()
        
        if 'choices' in response_data and response_data['choices']:
            return response_data['choices'][0]['message']['content']
        else:
            raise ValueError("No response from OpenAI API")
            
    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed: {e}")


if __name__ == "__main__":
    # Example usage - update the image path as needed
    image_path = "python/Accessorize Black_White Flute Sleeve Jacquard Dress (E65195).jpg"  # Use existing image in repo
    
    try:
        result = analyze_clothing_image(image_path)
        print(result)
    except Exception as e:
        print(f"Error: {e}")
        print("\nTo use this script:")
        print("1. Set your OpenAI API key: export OPENAI_API_KEY='your-key-here'")
        print("2. Update the image_path variable to point to your image")