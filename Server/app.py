from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
from dotenv import load_dotenv
import requests  # <-- Needed for Otpless verification API call
import google.generativeai as genai

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OTPLESS_SECRET_KEY = os.getenv("OTPLESS_SECRET_KEY")  # Add this in your .env

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from .env file.")

if not OTPLESS_SECRET_KEY:
    raise ValueError("OTPLESS_SECRET_KEY is missing from .env file.")

genai.configure(api_key=GEMINI_API_KEY)

# Initialize Flask
app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "UpLyft Backend is running! 🚀"

@app.route("/api/test")
def test():
    return "✅ Test route working!"

@app.route("/api/products", methods=["GET"])
def get_products():
    try:
        print("📦 Fetching products from database...")
        conn = sqlite3.connect("products.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, product_name, description, price, category, image_url FROM products")
        rows = cursor.fetchall()
        conn.close()

        products = [
            {
                "id": row[0],
                "product_name": row[1],
                "description": row[2],
                "price": row[3],
                "category": row[4],
                "image_url": row[5]
            } for row in rows
        ]
        return jsonify(products)

    except Exception as e:
        print(f"❌ Error fetching products: {e}")
        return jsonify({"error": str(e)}), 500

# 🧠 Gemini Chat — Fun & Flexible Assistant
@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "")

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        # Step 1: Load product catalog
        conn = sqlite3.connect("products.db")
        cursor = conn.cursor()
        cursor.execute("SELECT product_name, description FROM products")
        rows = cursor.fetchall()
        conn.close()

        catalog = "\n".join([f"{name}: {desc}" for name, desc in rows])

        # Step 2: Friendly & Fun system prompt
        system_prompt = f"""
You are UpLyft Assistant 🤖🛍️ — witty, helpful, and full of energy!

Here's the UpLyft product catalog:
--- CATALOG START ---
{catalog}
--- CATALOG END ---

Guidelines:
1. If the user asks about any product (or something similar), give helpful answers based on the catalog using emojis and fun tone.
2. If they ask something weird or off-topic (e.g. aliens, love life, Elon Musk):
   - Respond playfully 🤪 and bring the conversation back to products.
   - DO NOT say "invalid" or "I can't help".
   - Say something funny, sarcastic, or imaginative.
3. If you're unsure, make a fun guess and redirect them gently.
4. Be confident, charming, and never boring 😄

Example:
User: do you sell watches?
Assistant: ⌚ Hmm, I wish we did! But no watches here yet. Wanna see what’s hot in our current collection? 🔥

Now answer this:

User: {user_message}
Assistant:
"""

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(system_prompt)

        if hasattr(response, "text"):
            return jsonify({"reply": response.text})
        else:
            return jsonify({"error": "No valid response from Gemini."}), 500

    except Exception as e:
        print(f"❌ Error in /api/chat: {e}")
        return jsonify({"error": str(e)}), 500


# ----------- NEW: Otpless verification endpoint -----------

@app.route("/api/auth/otpless-verify", methods=["POST"])
def otpless_verify():
    try:
        data = request.get_json()
        token = data.get("otplessToken")

        if not token:
            return jsonify({"message": "Missing otplessToken"}), 400

        # Otpless verification API URL (check Otpless docs if this changes)
        verify_url = "https://api.otpless.com/v1/token/verify"

        headers = {
            "Authorization": f"Bearer {OTPLESS_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "token": token
        }

        response = requests.post(verify_url, json=payload, headers=headers)

        if response.status_code != 200:
            return jsonify({
                "message": "Otpless token verification failed",
                "details": response.text
            }), 401

        verify_data = response.json()

        # Extract user info from the verify_data - adjust this based on actual Otpless response
        user_info = {
            "name": verify_data.get("user", {}).get("name", "UpLyft User"),
            "email": verify_data.get("user", {}).get("email", ""),
            "mobile": verify_data.get("user", {}).get("mobile", "")
        }

        # TODO: Generate your own app auth token (e.g., JWT) here for frontend use
        app_token = "dummy-auth-token-for-demo"

        return jsonify({
            "token": app_token,
            "user": user_info
        }), 200

    except Exception as e:
        print(f"❌ Error in /api/auth/otpless-verify: {e}")
        return jsonify({"message": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(debug=True)
