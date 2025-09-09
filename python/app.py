import os
import io
import base64
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEBUG_LOG_OPENAI = True

PUBLIC_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "react-lens-luxe", "public")
)
PUBLIC_IMAGES = os.path.join(PUBLIC_ROOT, "images")
print("[startup] PUBLIC_ROOT =", PUBLIC_ROOT)

TYPE_TO_FOLDERS = {
    "long dress": ["dresses"],
    "short dress": ["dresses"],
    "long skirt": ["skirts"],
    "short skirt": ["skirts"],
    "pants": ["trousers", "jeans", "leggings"],
    "shorts": ["shorts"],
    "button-up shirt": ["shirts", "tops"],
    "hoodie": ["tops", "knitwear"],
    "jacket": ["tops", "knitwear"],
    "oversized t-shirt": ["tops"],
    "default": [
        "dresses", "skirts", "trousers", "jeans", "leggings",
        "tops", "shorts", "shirts", "knitwear"
    ],
}


def analyze_image_with_ai(image_data: bytes):
    """Use OpenAI to analyze the uploaded image and return (clothing_type, colors)."""
    try:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set")

        base64_image = base64.b64encode(image_data).decode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        }

        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "i want you to return 2 things in 2 different lines: first line is going to be the type "
                                "of clothing in the image. you will return it by the subcategories ahead: for dresses, "
                                "return either long dress or short dress. for skirts, return either long skirt or short "
                                "skirt. for pants, return either pants or shorts. for upperwear, return either button-up "
                                "shirt, hoodie, jacket or oversized t-shirt. second line is going to be the color of the "
                                "clothing in the image. return 3 colors maximum if the clothing has a few colors (the main ones)."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            ],
            "max_tokens": 300,
        }

        resp = requests.post(
            "https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=60
        )

        if DEBUG_LOG_OPENAI:
            print("[openai] status:", resp.status_code)
            print("[openai] body:", resp.text[:500])

        data = resp.json()
        if resp.status_code != 200:
            raise RuntimeError(f"OpenAI error {resp.status_code}: {data}")

        if not data.get("choices"):
            raise RuntimeError("OpenAI returned no choices")

        content = data["choices"][0]["message"]["content"]
        lines = [ln.strip() for ln in content.strip().split("\n") if ln.strip()]

        clothing_type = lines[0].lower() if len(lines) > 0 else ""
        colors = lines[1].lower() if len(lines) > 1 else ""
        return clothing_type, colors

    except Exception as e:
        print("[analyze_image_with_ai] ERROR:", e)
        return None, None


def find_similar_clothes(clothing_type: str, colors: str):
    """
    Scan /public/images/<folder> and score by color hits in filename.
    Returns a list of {filename, category, image_url, score}.
    """
    try:
        folders = TYPE_TO_FOLDERS.get(clothing_type, TYPE_TO_FOLDERS["default"])

        color_words = []
        if colors:
            color_words = (
                colors.replace(",", " ").replace("and", " ").lower().split()
            )

        candidates = []
        for folder in folders:
            abs_dir = os.path.join(PUBLIC_IMAGES, folder)
            if not os.path.isdir(abs_dir):
                continue

            for fname in os.listdir(abs_dir):
                if not fname.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                    continue

                score = 0
                lower = fname.lower()
                for c in color_words:
                    c = c.strip()
                    if len(c) > 2 and c in lower:
                        score += 1

                candidates.append(
                    {
                        "filename": fname,
                        "category": folder,
                        "image_url": f"http://localhost:3000/images/{folder}/{fname}",
                        "score": score,
                    }
                )

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:12]

    except Exception as e:
        print("[find_similar_clothes] ERROR:", e)
        return []


@app.post("/api/search")
def search_clothes():
    """Upload image and get similar clothes (no Mongo/GridFS)."""
    try:
        if "image" not in request.files:
            return jsonify({"error": 'No image uploaded (field name must be "image")'}), 400

        image_data = request.files["image"].read()

        clothing_type, colors = analyze_image_with_ai(image_data)
        if not clothing_type:
            return jsonify({"error": "Could not analyze image via OpenAI"}), 502

        similar_items = find_similar_clothes(clothing_type, colors)

        return jsonify(
            {
                "clothing_type": clothing_type,
                "colors": colors,
                "similar_items": similar_items,
                "total_found": len(similar_items),
            }
        )
    except Exception as e:
        print("[/api/search] ERROR:", e)
        return jsonify({"error": str(e)}), 500

@app.get("/api/health")
def health():
    return jsonify({
        "ok": True,
        "public_images_exists": os.path.isdir(PUBLIC_IMAGES),
        "has_openai_key": bool(OPENAI_API_KEY)
    })

if __name__ == "__main__":
    print("Starting LensAndLuxe server...")
    app.run(debug=True, port=5000)