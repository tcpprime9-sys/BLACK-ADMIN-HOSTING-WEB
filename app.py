from flask import Flask, render_template, request, redirect, url_for, session, send_file
import os
import zipfile
import subprocess
import signal
import shutil
import json
from functools import wraps

app = Flask(__name__)
app.secret_key = "BLACK_ADMIN_FINAL_SECURE_TOKEN_999"

# --- Master Admin Credentials ---
ADMIN_USERNAME = "BLACK"
ADMIN_PASSWORD = "BLACK_777"

UPLOAD_FOLDER = "uploads"
USER_DATA_FILE = "users.json"
MAX_RUNNING = 1 

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
processes = {}

# ---------- Security Decorators ----------

# Admin protection
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# User protection
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

# ---------- Helper Functions ----------

def get_user_upload_path(user):
    user_dir = os.path.join(UPLOAD_FOLDER, user)
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def start_app(user, app_name):
    user_dir = get_user_upload_path(user)
    app_dir = os.path.join(user_dir, app_name)
    extract_dir = os.path.join(app_dir, "extracted")
    log_path = os.path.join(app_dir, "logs.txt")
    
    main_file = None
    for f in ["main.py", "app.py", "bot.py"]:
        if os.path.exists(os.path.join(extract_dir, f)):
            main_file = f
            break
            
    if not main_file: return

    log = open(log_path, "a")
    p = subprocess.Popen(["python3", main_file], cwd=extract_dir, stdout=log, stderr=log)
    processes[(user, app_name)] = p

def stop_app(user, app_name):
    key = (user, app_name)
    p = processes.get(key)
    if p:
        p.send_signal(signal.SIGTERM)
        processes.pop(key, None)

# ---------- Routes ----------

@app.route("/login", methods=["GET", "POST"])
def login():
    if 'username' in session and not session.get('is_admin'):
        return redirect(url_for("index"))

    if request.method == "POST":
        u = request.form.get("username").strip()
        p = request.form.get("access_key").strip()
        users = load_users()
        
        if u in users:
            if users[u] == p:
                session['username'] = u
                session['is_admin'] = False
                return redirect(url_for("index"))
            return redirect(url_for("login"))
        else:
            users[u] = p
            save_users(users)
            session['username'] = u
            session['is_admin'] = False
            return redirect(url_for("index"))
        
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
        </body>
    '''

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    user_dir = get_user_upload_path(session['username'])
    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename.endswith(".zip"):
            app_name = file.filename.replace(".zip", "")
            app_dir = os.path.join(user_dir, app_name)
            os.makedirs(app_dir, exist_ok=True)
            file.save(os.path.join(app_dir, "app.zip"))

    apps = []
    if os.path.exists(user_dir):
        for name in os.listdir(user_dir):
            app_dir = os.path.join(user_dir, name)
            if not os.path.isdir(app_dir): continue
            log_file = os.path.join(app_dir, "logs.txt")
            log_data = ""
            if os.path.exists(log_file):
                with open(log_file, "r", errors="ignore") as f: log_data = f.read()[-3000:]
            apps.append({"name": name, "running": (session['username'], name) in processes, "log": log_data})
    return render_template("index.html", apps=apps)

@app.route("/run/<name>")
@login_required
def run(name):
    if (session['username'], name) not in processes and len(processes) < MAX_RUNNING:
        start_app(session['username'], name)
    return redirect(url_for("index"))

@app.route("/stop/<name>")
@login_required
def stop(name):
    stop_app(session['username'], name)
    return redirect(url_for("index"))

@app.route("/delete/<name>")
@login_required
def delete(name):
    stop_app(session['username'], name)
    user_dir = get_user_upload_path(session['username'])
    app_dir = os.path.join(user_dir, name)
    if os.path.exists(app_dir): shutil.rmtree(app_dir)
    return redirect(url_for("index"))

# ---------- Admin Routes ----------

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if session.get('is_admin'): return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        u = request.form.get("u")
        p = request.form.get("p")
        if u == ADMIN_USERNAME and p == ADMIN_PASSWORD:
            session.clear()
            session['username'] = u
            session['is_admin'] = True
            return redirect(url_for("admin_dashboard"))
        return '<script>alert("Invalid!"); window.location="/admin";</script>'
    return '''
        <body style="background:#050505; color:white; text-align:center; padding-top:100px; font-family:Arial;">
            <h2 style="color:#ff3333;">🛡️ MASTER ADMIN</h2>
            <form method="post" style="background:#111; display:inline-block; padding:40px; border-radius:10px; border:2px solid #ff3333;">
                <input type="text" name="u" placeholder="Admin ID" required style="padding:12px; margin-bottom:10px; width:250px;"><br>
                <input type="password" name="p" placeholder="Admin Password" required style="padding:12px; margin-bottom:20px; width:250px;"><br>
                <button type="submit" style="padding:12px 20px; background:#ff3333; color:white; border:none; border-radius:5px; font-weight:bold; width:100%;">ENTER</button>
            </form>
        </body>
    '''

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    all_data = []
    if os.path.exists(UPLOAD_FOLDER):
        for user_name in os.listdir(UPLOAD_FOLDER):
            user_path = os.path.join(UPLOAD_FOLDER, user_name)
            if os.path.isdir(user_path):
                user_apps = []
                for app_name in os.listdir(user_path):
                    user_apps.append({"name": app_name, "running": (user_name, app_name) in processes})
                all_data.append({"username": user_name, "apps": user_apps})
    
    rows = ""
    for u in all_data:
        for a in u['apps']:
            status = 'RUNNING' if a['running'] else 'STOPPED'
            rows += f'<tr><td>{u["username"]}</td><td>{a["name"]}</td><td>{status}</td><td><a href="/admin/action/stop/{u["username"]}/{a["name"]}">Stop</a></td></tr>'
            
    return f'<body><h1>Admin Dashboard</h1><table>{rows}</table><br><a href="/logout">Logout</a></body>'

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8030)