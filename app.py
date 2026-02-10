from flask import Flask, render_template, request, redirect, url_for, session, send_file
import os
import zipfile
import subprocess
import signal
import shutil
import json
import sys
from functools import wraps

app = Flask(__name__)
app.secret_key = "BLACK_ADMIN_ORIGINAL_LOOK_RENDER_FIX"

# --- Master Admin Credentials ---
ADMIN_USERNAME = "BLACK"
ADMIN_PASSWORD = "BLACK_777"

UPLOAD_FOLDER = "uploads"
USER_DATA_FILE = "users.json"
MAX_RUNNING = 5

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
processes = {}

# ---------- Security Decorators ----------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ---------- Database logic ----------
def load_users():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_users(users):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(users, f)

# ---------- Helper Functions (Render & Requirements Fix) ----------
def start_app(user, app_name):
    user_dir = os.path.join(UPLOAD_FOLDER, user)
    app_dir = os.path.join(user_dir, app_name)
    zip_path = os.path.join(app_dir, "app.zip")
    extract_dir = os.path.join(app_dir, "extracted")
    log_path = os.path.join(app_dir, "logs.txt")

    if not os.path.exists(zip_path): return

    if os.path.exists(extract_dir): shutil.rmtree(extract_dir, ignore_errors=True)
    os.makedirs(extract_dir, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(extract_dir)

    found_main = None
    target_dir = extract_dir
    
    for root, dirs, files in os.walk(extract_dir):
        # Requirements Installation Fix for Render
        if "requirements.txt" in files:
            req_path = os.path.join(root, "requirements.txt")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_path])
            except:
                pass
            
        for f in files:
            if f in ["main.py", "app.py", "bot.py"]:
                found_main = os.path.join(root, f)
                target_dir = root
                break
        if found_main: break

    if found_main:
        log = open(log_path, "a")
        # sys.executable use kora hoyeche Render-er jonno
        p = subprocess.Popen([sys.executable, os.path.basename(found_main)], 
                             cwd=target_dir, stdout=log, stderr=log)
        processes[(user, app_name)] = p

def stop_app(user, app_name):
    key = (user, app_name)
    p = processes.get(key)
    if p:
        try:
            os.kill(p.pid, signal.SIGKILL) 
        except:
            pass
        processes.pop(key, None)

# ---------- Login Route (Original Glow Design) ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if 'username' in session: return redirect(url_for("index"))
    if request.method == "POST":
        u, p = request.form.get("username").strip(), request.form.get("access_key").strip()
        users = load_users()
        if u in users and users[u] == p:
            session['username'] = u
            return redirect(url_for("index"))
        elif u not in users:
            users[u] = p
            save_users(users)
            session['username'] = u
            return redirect(url_for("index"))
        return redirect(url_for("login"))
        
    return '''
        <body style="background:#0d0d0d; color:white; text-align:center; padding-top:100px; font-family:Arial;">
            <h2 style="color:#00ffcc; letter-spacing: 2px;">🔥 BLACK ADMIN HOSTING LOGIN 🔥</h2>
            <div style="background:#1a1a1a; display:inline-block; padding:40px; border-radius:15px; border: 1px solid #00ffcc; box-shadow: 0 0 15px #00ffcc33;">
                <p style="color:#888; margin-bottom:20px;">Enter Username & Password (Visible)</p>
                <form method="post" autocomplete="off">
                    <input type="text" name="username" placeholder="Username" required 
                           style="padding:12px; border-radius:5px; border:1px solid #333; width:250px; background:#222; color:white; margin-bottom:15px;"><br>
                    <input type="text" name="access_key" placeholder="Password" required 
                           style="padding:12px; border-radius:5px; border:1px solid #333; width:250px; background:#222; color:white; margin-bottom:20px;"><br>
                    <button type="submit" style="padding:12px 30px; background:#00ffcc; border:none; border-radius:5px; cursor:pointer; font-weight:bold; color:black; width:100%;">ACCESS PANEL</button>
                </form>
            </div>
            <p style="margin-top:20px; font-size:12px; color:#444;">Powered by BLACK ADMIN © 2026</p>
        </body>
    '''

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    user_dir = os.path.join(UPLOAD_FOLDER, session['username'])
    os.makedirs(user_dir, exist_ok=True)
    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename.endswith(".zip"):
            app_name = file.filename.replace(".zip", "")
            app_dir = os.path.join(user_dir, app_name)
            if os.path.exists(app_dir): shutil.rmtree(app_dir, ignore_errors=True)
            os.makedirs(app_dir, exist_ok=True)
            file.save(os.path.join(app_dir, "app.zip"))
            return redirect(url_for("index"))
    
    apps = []
    if os.path.exists(user_dir):
        for name in os.listdir(user_dir):
            app_dir = os.path.join(user_dir, name)
            if os.path.isdir(app_dir):
                log_file = os.path.join(app_dir, "logs.txt")
                log_data = open(log_file, "r").read()[-500:] if os.path.exists(log_file) else "No logs."
                apps.append({"name": name, "running": (session['username'], name) in processes, "log": log_data})
    return render_template("index.html", apps=apps)

@app.route("/run/<name>")
@login_required
def run_app_route(name):
    user_running = [k for k in processes.keys() if k[0] == session['username']]
    for k in user_running: stop_app(k[0], k[1])
    start_app(session['username'], name)
    return redirect(url_for("index"))

@app.route("/stop/<name>")
@login_required
def stop_app_route(name):
    stop_app(session['username'], name)
    return redirect(url_for("index"))

@app.route("/delete/<name>")
@login_required
def delete_app_route(name):
    stop_app(session['username'], name)
    user_dir = os.path.join(UPLOAD_FOLDER, session['username'])
    app_dir = os.path.join(user_dir, name)
    if os.path.exists(app_dir):
        shutil.rmtree(app_dir, ignore_errors=True)
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8030))
    app.run(host="0.0.0.0", port=port)
