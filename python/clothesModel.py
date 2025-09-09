import os
from openai import OpenAI
import requests
import base64


def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

key = "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"
image_path="C:\\Users\\ofeka\\Downloads\\bottomwear_skirt1008-1.png"
base64_image = encode_image(image_path)
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {key}"
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

response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
response_data = response.json()

image_description = response_data['choices'][0]['message']['content'] if response_data['choices'] else ''
print(image_description)