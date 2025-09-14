import os
import io
import json, re
import base64
import requests
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from dotenv import load_dotenv
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta

app = Flask(__name__)

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEBUG_LOG_OPENAI = True

# session config
app.secret_key = os.getenv('SECRET_KEY', 'my-secret-key-for-final-project')
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

CORS(app, supports_credentials=True, origins=['http://localhost:3000'])

# database connection without specifying database initially
initial_db_config = {
    'host': 'localhost',
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'charset': 'utf8mb4'
}

# database config with lens_luxe database
db_config = {
    'host': 'localhost',
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': 'lens_luxe',
    'charset': 'utf8mb4'
}

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

def connect_to_db(use_database=True):
    try:
        config = db_config if use_database else initial_db_config
        conn = mysql.connector.connect(**config)
        return conn
    except mysql.connector.Error as err:
        print(f"DB connection error: {err}")
        return None

def setup_database():
    # first connect without specifying database
    conn = connect_to_db(use_database=False)
    if conn:
        cursor = conn.cursor()
        try:
            # create the database if it doesn't exist
            cursor.execute("CREATE DATABASE IF NOT EXISTS lens_luxe")
            print("Database 'lens_luxe' created or already exists")
            
            # now switch to the lens_luxe database
            cursor.execute("USE lens_luxe")
            
            # create users table based on our schema
            user_table = """
            CREATE TABLE IF NOT EXISTS users (
                email VARCHAR(255) PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                gender ENUM('male', 'female', 'other') NOT NULL,
                age INT NOT NULL,
                phone VARCHAR(20) NOT NULL,
                address VARCHAR(255) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(user_table)
            conn.commit()
            print("Database setup complete")
        except mysql.connector.Error as err:
            print(f"Database setup error: {err}")
        finally:
            cursor.close()
            conn.close()

# decorator to check if user is logged in
def login_required(f):
    def wrapper(*args, **kwargs):
        if 'user_email' not in session:
            return jsonify({'error': 'You need to login first'}), 401
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/api/signup', methods=['POST'])
def create_account():
    data = request.get_json()
    
    # check all fields are there
    required = ['firstName', 'lastName', 'gender', 'age', 'email', 'phone', 'address', 'password']
    for field in required:
        if field not in data or not data[field]:
            return jsonify({'error': f'{field} is required'}), 400
    
    email = data['email'].lower().strip()
    if '@' not in email:
        return jsonify({'error': 'Please enter a valid email'}), 400
    
    if len(data['password']) < 6:
        return jsonify({'error': 'Password needs to be at least 6 characters'}), 400
    
    # hash password for security
    hashed_password = generate_password_hash(data['password'])
    
    conn = connect_to_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    
    try:
        # check if user already exists
        cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'error': 'Account with this email already exists'}), 409
        
        # create new user
        insert_user = """
        INSERT INTO users (email, first_name, last_name, gender, age, phone, address, password_hash)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_user, (
            email,
            data['firstName'],
            data['lastName'],
            data['gender'],
            int(data['age']),
            data['phone'],
            data['address'],
            hashed_password
        ))
        
        conn.commit()
        
        # log them in automatically
        session.permanent = True
        session['user_email'] = email
        session['user_name'] = f"{data['firstName']} {data['lastName']}"
        
        return jsonify({
            'message': 'Account created successfully',
            'user': {
                'email': email,
                'firstName': data['firstName'],
                'lastName': data['lastName']
            }
        }), 201
        
    except mysql.connector.Error as err:
        return jsonify({'error': f'Database error: {str(err)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Something went wrong: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/login', methods=['POST'])
def user_login():
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    email = data['email'].lower().strip()
    password = data['password']
    
    conn = connect_to_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    
    try:
        # find user in database
        cursor.execute("""
            SELECT email, first_name, last_name, password_hash 
            FROM users WHERE email = %s
        """, (email,))
        
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # check if password matches
        if not check_password_hash(user[3], password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # create session
        session.permanent = True
        session['user_email'] = user[0]
        session['user_name'] = f"{user[1]} {user[2]}"
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'email': user[0],
                'firstName': user[1],
                'lastName': user[2]
            }
        }), 200
        
    except mysql.connector.Error as err:
        return jsonify({'error': f'Database error: {str(err)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Login error: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/logout', methods=['POST'])
def user_logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/api/check-auth', methods=['GET'])
def check_login_status():
    if 'user_email' in session:
        return jsonify({
            'authenticated': True,
            'user': {
                'email': session['user_email'],
                'name': session['user_name']
            }
        }), 200
    else:
        return jsonify({'authenticated': False}), 401

@app.route('/api/profile', methods=['GET'])
@login_required
def get_user_profile():
    user_email = session['user_email']
    
    conn = connect_to_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    
    try:
        # fetch complete user profile
        cursor.execute("""
            SELECT email, first_name, last_name, gender, age, phone, address, created_at
            FROM users WHERE email = %s
        """, (user_email,))
        
        user_data = cursor.fetchone()
        
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        # format the response
        profile_data = {
            'email': user_data[0],
            'first_name': user_data[1],
            'last_name': user_data[2],
            'gender': user_data[3],
            'age': user_data[4],
            'phone': user_data[5],
            'address': user_data[6],
            'created_at': user_data[7].isoformat() if user_data[7] else None
        }
        
        return jsonify({
            'user': profile_data
        }), 200
        
    except mysql.connector.Error as err:
        return jsonify({'error': f'Database error: {str(err)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Profile fetch error: {str(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

# existing image analysis function
def analyze_image_with_ai(image_data: bytes):
    try:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set")

        base64_image = base64.b64encode(image_data).decode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        }

        # prompt for the AI to analyze clothing
        system_prompt = (
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
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "max_tokens": 300,
            "temperature": 0.1,
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=60
        )

        if DEBUG_LOG_OPENAI:
            print("[openai] status:", response.status_code)
            print("[openai] body:", response.text[:500])

        if response.status_code != 200:
            raise RuntimeError(f"OpenAI error {response.status_code}: {response.text[:500]}")

        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

        # extract JSON from response
        json_match = re.search(r"\{.*\}", content, flags=re.S)
        json_str = json_match.group(0) if json_match else content

        analysis = json.loads(json_str)

        # clean up the analysis
        analysis["category"] = (analysis.get("category") or "").lower()
        analysis["colors"] = [c.lower() for c in (analysis.get("colors") or [])][:3]
        analysis["length"] = (analysis.get("length") or None)
        analysis["keywords"] = [k.lower() for k in (analysis.get("keywords") or [])]

        return analysis

    except Exception as e:
        print("[analyze_image_with_ai] ERROR:", e)
        return None

def get_folders_for_category(category: str):
    # map categories to our folder structure
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

def find_similar_clothes(analysis: dict, max_results: int = 8):
    try:
        category = (analysis.get("category") or "").lower()
        colors = [c.lower() for c in (analysis.get("colors") or [])]
        length = (analysis.get("length") or "").lower()
        keywords = [k.lower() for k in (analysis.get("keywords") or [])]

        search_folders = get_folders_for_category(category)

        # color mappings for better matching
        color_synonyms = {
            "white": ["white", "ivory", "cream", "ecru", "offwhite", "off-white"],
            "black": ["black"],
            "red": ["red", "burgundy", "wine"],
            "green": ["green", "khaki", "sage", "olive"],
            "blue": ["blue", "navy", "indigo", "teal", "aqua"],
            "pink": ["pink", "rose", "blush", "fuchsia"],
            "beige": ["beige", "stone", "sand", "camel", "tan"],
            "grey": ["grey", "gray", "charcoal"],
            "brown": ["brown", "chocolate", "mocha"],
            "yellow": ["yellow", "mustard"],
            "purple": ["purple", "lilac", "lavender", "violet"],
            "orange": ["orange", "rust", "terracotta"],
        }

        # patterns that indicate multiple colors
        multi_color_patterns = {
            "stripe", "striped", "stripes", "floral", "flower", "print", "pattern",
            "leopard", "zebra", "animal", "check", "checked", "plaid", "polka", "dot",
            "spots", "spot", "multi", "multicolour", "multicolor", "colourblock", "colorblock"
        }

        # keyword variations for better matching
        keyword_variations = {
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

        length_variations = {
            "maxi": ["maxi", "long"],
            "midi": ["midi"],
            "mini": ["mini", "short"],
            "short": ["short", "mini"],
            "long": ["long", "maxi"],
            "cropped": ["crop", "cropped"],
        }
        length_terms = length_variations.get(length, [])

        # build allowed color terms
        allowed_colors = set()
        for color in colors:
            allowed_colors.update(color_synonyms.get(color, [color]))

        # build disallowed color terms
        disallowed_colors = set()
        if colors:
            for color_name, synonyms in color_synonyms.items():
                if color_name not in colors:
                    disallowed_colors.update(synonyms)

        def tokenize_filename(filename: str):
            # split filename into tokens for matching
            tokens = re.split(r"[\s_\-\(\),\.]+", filename.lower())
            return [token for token in tokens if token]

        scored_items = []
        for folder in search_folders:
            folder_path = os.path.join(PUBLIC_IMAGES, folder)
            if not os.path.isdir(folder_path):
                continue

            for filename in os.listdir(folder_path):
                if not filename.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                    continue

                tokens = tokenize_filename(filename)

                # score based on color matching
                color_matches = sum(1 for color in allowed_colors if color in tokens) if allowed_colors else 0
                color_conflicts = sum(1 for color in disallowed_colors if color in tokens) if disallowed_colors else 0
                has_pattern = any(pattern in tokens for pattern in multi_color_patterns)

                # strict color filtering for single color searches
                if len(colors) == 1:
                    if color_matches == 0:
                        continue
                    if color_conflicts > 0:
                        continue
                    if has_pattern:
                        continue
                elif len(colors) > 1 and allowed_colors and color_matches == 0:
                    continue

                # calculate similarity score
                score = 0
                score += color_matches * 4
                score -= color_conflicts * 3

                # bonus for length matching
                for length_term in length_terms:
                    if length_term in tokens:
                        score += 2

                # bonus for keyword matching
                for keyword in keywords:
                    variations = keyword_variations.get(keyword, [keyword])
                    if any(var in tokens for var in variations):
                        score += 2

                # bonus for category matching
                if category and category in tokens:
                    score += 1

                scored_items.append({
                    "filename": filename,
                    "category": folder,
                    "image_url": f"http://localhost:3000/images/{folder}/{filename}",
                    "score": score,
                })

        # sort by score and return top results
        scored_items.sort(key=lambda x: x["score"], reverse=True)
        return scored_items[:max_results]

    except Exception as e:
        print("[find_similar_clothes] ERROR:", e)
        return []

@app.route("/api/search", methods=['POST'])
@login_required  # user must be logged in to search
def search_for_clothes():
    try:
        if "image" not in request.files:
            return jsonify({"error": 'No image uploaded'}), 400

        image_file = request.files["image"]
        image_data = image_file.read()

        # analyze the uploaded image
        analysis = analyze_image_with_ai(image_data)
        if not analysis:
            return jsonify({"error": "Could not analyze the image"}), 502

        # find similar clothing items
        similar_items = find_similar_clothes(analysis)

        return jsonify({
            "clothing_type": analysis.get("category"),
            "colors": ", ".join(analysis.get("colors") or []),
            "similar_items": similar_items,
            "total_found": len(similar_items),
            "searched_by": session['user_email']
        })

    except Exception as e:
        print("[search] ERROR:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/health", methods=['GET'])
def health_check():
    return jsonify({
        "status": "running",
        "images_folder_exists": os.path.isdir(PUBLIC_IMAGES),
        "openai_configured": bool(OPENAI_API_KEY),
        "database_accessible": bool(connect_to_db())
    })

if __name__ == "__main__":
    print("Setting up database...")
    setup_database()
    
    print("Starting Lens&Luxe server...")
    app.run(debug=True, port=5001)