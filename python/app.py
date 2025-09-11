import os
import io
import json, re
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
    """
    Ask the model for compact, universal JSON. It works for all types because:
    - 'category' picks a broad bucket we already map to folders
    - 'colors' is up to 3 main colors
    - 'length' is optional (mini/midi/maxi/short/long/cropped)
    - 'keywords' is a short list of generic attributes (e.g., 'slit', 'button-front', 'strap', 'wide-leg', 'ribbed')
    """
    try:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set")

        base64_image = base64.b64encode(image_data).decode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        }

        sys_text = (
            "You are a fashion tagging assistant. Return JSON ONLY. No prose."
            " Schema: {"
            '  "category": one of ["dress","skirt","pants","shorts","jeans","leggings","shirt","top","hoodie","jacket","knitwear"],'
            '  "colors": array of 1-3 lowercase color words (e.g., ["white","black","beige"]),'
            '  "length": one of ["mini","midi","maxi","short","long","cropped", null],'
            '  "keywords": array of 3-8 short lowercase tokens describing visible features that typically appear in product filenames;'
            '              e.g. ["slit","strap","sleeveless","button-front","lace","pleated","floral","wide-leg","skinny","ribbed","denim","cargo"].'
            " Only include relevant fields; use null for length if not applicable."
            " Do not include explanations."
        )

        user_content = [
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
            }
        ]

        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": sys_text},
                {"role": "user", "content": user_content},
            ],
            "max_tokens": 300,
            "temperature": 0.1,
        }

        resp = requests.post(
            "https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=60
        )

        if DEBUG_LOG_OPENAI:
            print("[openai] status:", resp.status_code)
            print("[openai] body:", resp.text[:500])


        if resp.status_code != 200:
            raise RuntimeError(f"OpenAI error {resp.status_code}: {resp.text[:500]}")

        data = resp.json()
        msg = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

        m = re.search(r"\{.*\}", msg, flags=re.S)
        json_str = m.group(0) if m else msg

        meta = json.loads(json_str)

        meta["category"] = (meta.get("category") or "").lower()
        meta["colors"] = [c.lower() for c in (meta.get("colors") or [])][:3]
        meta["length"] = (meta.get("length") or None)
        meta["keywords"] = [k.lower() for k in (meta.get("keywords") or [])]

        return meta

    except Exception as e:
        print("[analyze_image_with_ai] ERROR:", e)
        return None

def folders_for_category(category: str):
    if category == "dress":
        return ["dresses"]
    if category == "skirt":
        return ["skirts"]
    if category == "pants":
        return ["trousers", "jeans", "leggings"]
    if category == "shorts":
        return ["shorts"]
    if category == "jeans":
        return ["jeans"]
    if category == "leggings":
        return ["leggings"]
    if category in ("shirt", "top"):
        return ["shirts", "tops"]
    if category == "hoodie":
        return ["tops", "knitwear"]
    if category == "jacket":
        return ["tops", "knitwear"]
    if category == "knitwear":
        return ["knitwear", "tops"]
    return TYPE_TO_FOLDERS["default"]

def find_similar_clothes(meta: dict, max_results: int = 8):
    """
    Strong color focus:
      - If exactly ONE color predicted → only keep items with that color and
        exclude filenames indicating other colors / multi-color patterns.
      - If multiple colors predicted → require ≥1 allowed color hit, then score.
    """
    try:
        category = (meta.get("category") or "").lower()
        colors   = [c.lower() for c in (meta.get("colors") or [])]
        length   = (meta.get("length") or "").lower()
        keywords = [k.lower() for k in (meta.get("keywords") or [])]

        folders = folders_for_category(category)

        COLOR_SYNS = {
            "white":  ["white", "ivory", "cream", "ecru", "offwhite", "off-white"],
            "black":  ["black"],
            "red":    ["red", "burgundy", "wine"],
            "green":  ["green", "khaki", "sage", "olive"],
            "blue":   ["blue", "navy", "indigo", "teal", "aqua"],
            "pink":   ["pink", "rose", "blush", "fuchsia"],
            "beige":  ["beige", "stone", "sand", "camel", "tan"],
            "grey":   ["grey", "gray", "charcoal"],
            "brown":  ["brown", "chocolate", "mocha"],
            "yellow": ["yellow", "mustard"],
            "purple": ["purple", "lilac", "lavender", "violet"],
            "orange": ["orange", "rust", "terracotta"],
        }

        MULTI_PATTERN = {
            "stripe","striped","stripes","floral","flower","print","pattern",
            "leopard","zebra","animal","check","checked","plaid","polka","dot",
            "spots","spot","multi","multicolour","multicolor","colourblock","colorblock"
        }

        syn = {
            "slit": ["slit", "split"],
            "strap": ["strap", "strappy", "spaghetti"],
            "sleeveless": ["sleeveless", "tank"],
            "button-front": ["button", "button-front", "buttoned"],
            "lace": ["lace", "lacy", "broderie", "eyelet"],
            "pleated": ["pleat", "pleated"],
            "ribbed": ["rib", "ribbed"],
            "denim": ["denim", "jean", "jeans"],
            "cargo": ["cargo", "utility"],
            "wide-leg": ["wide", "wide-leg", "palazzo", "flare", "flared"],
            "skinny": ["skinny", "slim"],
            "straight": ["straight"],
            "bodycon": ["bodycon", "fitted"],
            "wrap": ["wrap", "wrap-front", "wrapover", "surplice"],
        }
        length_map = {
            "maxi": ["maxi", "long"],
            "midi": ["midi"],
            "mini": ["mini", "short"],
            "short": ["short", "mini"],
            "long":  ["long", "maxi"],
            "cropped": ["crop", "cropped"],
        }
        length_terms = length_map.get(length, [])

        allowed_color_terms = set()
        for c in colors:
            allowed_color_terms.update(COLOR_SYNS.get(c, [c]))

        disallowed_color_terms = set()
        if colors:
            for name, syns in COLOR_SYNS.items():
                if name not in colors:
                    disallowed_color_terms.update(syns)

        def tokens(s: str):
            import re
            t = re.split(r"[\s_\-\(\),\.]+", s.lower())
            return [w for w in t if w]

        scored = []
        for folder in folders:
            abs_dir = os.path.join(PUBLIC_IMAGES, folder)
            if not os.path.isdir(abs_dir):
                continue

            for fname in os.listdir(abs_dir):
                if not fname.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                    continue

                toks = tokens(fname)

                allow_hits = sum(1 for v in allowed_color_terms if v in toks) if allowed_color_terms else 0
                disallow_hits = sum(1 for v in disallowed_color_terms if v in toks) if disallowed_color_terms else 0
                has_multi_pattern = any(p in toks for p in MULTI_PATTERN)

                if len(colors) == 1:
                    if allow_hits == 0:
                        continue
                    if disallow_hits > 0:
                        continue
                    if has_multi_pattern:
                        continue

                elif len(colors) > 1 and allowed_color_terms and allow_hits == 0:
                    continue

                score = 0
                score += allow_hits * 4  
                score -= disallow_hits * 3 
                for t in length_terms:
                    if t in toks:
                        score += 2

                for kw in keywords:
                    variants = syn.get(kw, [kw])
                    if any(v in toks for v in variants):
                        score += 2

                if category and category in toks:
                    score += 1

                scored.append({
                    "filename": fname,
                    "category": folder,
                    "image_url": f"http://localhost:3000/images/{folder}/{fname}",
                    "score": score,
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:max_results]

    except Exception as e:
        print("[find_similar_clothes] ERROR:", e)
        return []


@app.post("/api/search")
def search_clothes():

    try:
        if "image" not in request.files:
            return jsonify({"error": 'No image uploaded (field name must be "image")'}), 400

        image_data = request.files["image"].read()

        meta = analyze_image_with_ai(image_data)
        if not meta:
            return jsonify({"error": "Could not analyze image"}), 502

        similar_items = find_similar_clothes(meta)

        return jsonify({
            "clothing_type": meta.get("category"),
            "colors": ", ".join(meta.get("colors") or []),
            "similar_items": similar_items,
            "total_found": len(similar_items),
        })

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