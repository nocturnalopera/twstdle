from flask import Flask, render_template, request, jsonify, session, send_file
import os
import datetime
from datetime import timezone, timedelta
import hashlib
from twstdle_characters import charadict

app = Flask(__name__)
app.secret_key = "twstdle_secret_key"

# Rutas base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

IMAGES_DIR = os.path.join(BASE_DIR, "static", "images")
if not os.path.exists(IMAGES_DIR):
    IMAGES_DIR = os.path.join(BASE_DIR, "images")

ICON_PATH = os.path.join(BASE_DIR, "iconoiconopagina.png")
if not os.path.exists(ICON_PATH):
    ICON_PATH = os.path.join(BASE_DIR, "static", "iconoiconopagina.png")

FLECHA_PATH = os.path.join(BASE_DIR, "flecha.png")
if not os.path.exists(FLECHA_PATH):
    FLECHA_PATH = os.path.join(BASE_DIR, "static", "flecha.png")

VALID_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")

def _normalize(text):
    return text.strip().lower().replace(" ", "").replace("_", "").replace("-", "")

def find_character_image(character_name):
    if not os.path.isdir(IMAGES_DIR):
        return None
    target = _normalize(character_name)
    for filename in os.listdir(IMAGES_DIR):
        name, ext = os.path.splitext(filename)
        if _normalize(name) == target and ext.lower() in VALID_EXTENSIONS:
            return os.path.join(IMAGES_DIR, filename)
    return None

def get_today_utc6():
    """Obtiene la fecha actual fijada en la zona horaria UTC-6."""
    return datetime.datetime.now(timezone(timedelta(hours=-6)))

def get_daily_character():
    """Selecciona un personaje único basado en la fecha en UTC-6."""
    today_str = get_today_utc6().strftime("%Y-%m-%d")
    keys = sorted(list(charadict.keys()))
    date_hash = int(hashlib.md5(today_str.encode()).hexdigest(), 16)
    return keys[date_hash % len(keys)]

ATTRIBUTES = ["Occupation", "Dorm", "Grade", "Species", "Age", "School"]

@app.route("/")
def index():
    session["answer"] = get_daily_character()
    today_str = get_today_utc6().strftime("%Y-%m-%d")
    return render_template("index.html", characters=sorted(list(charadict.keys())), today_date=today_str)

@app.route("/image/<char_name>")
def serve_character_image(char_name):
    img_path = find_character_image(char_name)
    if img_path and os.path.exists(img_path):
        return send_file(img_path)
    return "", 404

@app.route("/logo")
def serve_logo():
    if os.path.exists(ICON_PATH):
        return send_file(ICON_PATH)
    return "", 404

@app.route("/flecha")
def serve_flecha():
    if os.path.exists(FLECHA_PATH):
        return send_file(FLECHA_PATH)
    return "", 404

@app.route("/guess", methods=["POST"])
def guess():
    data = request.get_json()
    guess_name = data.get("guess")
    answer_name = session.get("answer")

    if not guess_name or guess_name not in charadict:
        return jsonify({"error": "Character not found"}), 400

    guess_data = charadict[guess_name]
    answer_data = charadict[answer_name]

    results = {}
    for attr in ATTRIBUTES:
        g_val = str(guess_data[attr])
        a_val = str(answer_data[attr])
        
        if g_val == a_val:
            status = "correct"
        else:
            g_set = {item.strip().lower() for item in g_val.split(",")}
            a_set = {item.strip().lower() for item in a_val.split(",")}
            
            if g_set & a_set:
                status = "partial"
            elif (a_val.lower() in g_val.lower()) or (g_val.lower() in a_val.lower()):
                status = "partial"
            else:
                status = "wrong"

        results[attr] = {"value": g_val, "status": status}

    is_correct = (guess_name == answer_name)

    return jsonify({
        "guess": guess_name,
        "is_correct": is_correct,
        "attributes": results,
        "answer": answer_name if is_correct else None
    })

if __name__ == "__main__":
    app.run(debug=True)