from flask import Flask, render_template, request, redirect, url_for, session
import json
import requests
import os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your_secret_key")

# --- ThingSpeak API Setup ---
# Prefer environment variables in production; fallback values keep local dev working
THINGSPEAK_CHANNEL_ID = os.getenv("THINGSPEAK_CHANNEL_ID", "3145082")
THINGSPEAK_API_KEY = os.getenv("THINGSPEAK_API_KEY", "HF5NVG4EZ5GFZL5T")

# --- Local file for user accounts ---
USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

# --- Routes ---
@app.route("/")
def home():
    return redirect(url_for("signup"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        users = load_users()
        if username in users:
            return "User already exists. Try logging in."

        users[username] = {"password": password}
        save_users(users)
        return redirect(url_for("login"))

    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        users = load_users()
        if username in users and users[username]["password"] == password:
            session["username"] = username
            return redirect(url_for("dashboard"))
        return "Invalid credentials. Try again."

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))

    # --- Fetch ThingSpeak Data ---
    url = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds.json?api_key={THINGSPEAK_API_KEY}&results=5"
    response = requests.get(url).json()

    if "feeds" not in response:
        return "Error fetching data from ThingSpeak."

    channel_info = response.get("channel", {})
    feeds = response["feeds"]

    # Extract latest feed
    latest_data = feeds[-1] if feeds else {}

    data = {
        "channel_name": channel_info.get("name", "Unknown Channel"),
        "field1": latest_data.get("field1", "N/A"),
        "field2": latest_data.get("field2", "N/A"),
        "field3": latest_data.get("field3", "N/A"),
        "field4": latest_data.get("field4", "N/A"),
        "field5": latest_data.get("field5", "N/A"),
        "field6": latest_data.get("field6", "N/A"),
        "created_at": latest_data.get("created_at", "N/A")
    }

    return render_template("dashboard.html", data=data, username=session["username"])

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
