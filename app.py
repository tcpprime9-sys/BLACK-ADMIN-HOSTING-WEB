from flask import Flask, render_template, request, redirect, url_for, session, send_file
import os, zipfile, subprocess, signal, shutil, json, sys
from functools import wraps

app = Flask(__name__)
app.secret_key = "BLACK_ADMIN_3D_SUPREME_2026"

# --- Master Admin Credentials ---
ADMIN_USERNAME = "BLACK"
ADMIN_PASSWORD = "BLACK_777"

UPLOAD_FOLDER = "uploads"
USER_DATA_FILE = "users.json"
MAX_RUNNING = 1 

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
processes = {}

# ---------- Security ----------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session: return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'): return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def load_users():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_users(users):
    with open(USER_DATA_FILE, "w") as f: json.dump(users, f)

# ---------- Bot Logic ----------
def start_app(user, app_name):
    user_dir = os.path.join(UPLOAD_FOLDER, user)
    app_dir = os.path.join(user_dir, app_name)
    zip_path = os.path.join(app_dir, "app.zip")
    extract_dir = os.path.join(app_dir, "extracted")
    log_path = os.path.join(app_dir, "logs.txt")

    if not os.path.exists(zip_path): return
    shutil.rmtree(extract_dir, ignore_errors=True)
    os.makedirs(extract_dir, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'r') as z: z.extractall(extract_dir)

    found_main, target_dir = None, extract_dir
    for root, dirs, files in os.walk(extract_dir):
        if "requirements.txt" in files:
            try: subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", os.path.join(root, "requirements.txt")])
            except: pass
        for f in files:
            if f in ["main.py", "app.py", "bot.py"]:
                found_main = os.path.join(root, f); target_dir = root; break
        if found_main: break

    if found_main:
        log = open(log_path, "a")
        p = subprocess.Popen([sys.executable, os.path.basename(found_main)], cwd=target_dir, stdout=log, stderr=log)
        processes[(user, app_name)] = p

def stop_app(user, app_name):
    key = (user, app_name)
    p = processes.get(key)
    if p:
        try: os.kill(p.pid, signal.SIGKILL)
        except: pass
        processes.pop(key, None)

# ---------- [3D GLOW LOGIN] ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if 'username' in session and not session.get('is_admin'): return redirect(url_for("index"))
    if request.method == "POST":
        u, p = request.form.get("username").strip(), request.form.get("access_key").strip()
        users = load_users()
        if u in users and users[u] == p:
            session['username'], session['is_admin'] = u, False
            return redirect(url_for("index"))
        elif u not in users:
            users[u] = p; save_users(users)
            session['username'], session['is_admin'] = u, False
            return redirect(url_for("index"))
    return '''
    <body style="background:#050505; color:white; text-align:center; padding-top:100px; font-family:sans-serif; overflow:hidden;">
        <style>
            .container {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(15px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 25px 45px rgba(0,0,0,0.5), inset 0 0 15px rgba(0,255,204,0.2);
                border-radius: 20px;
                padding: 50px;
                display: inline-block;
                transform: perspective(1000px) rotateX(5deg);
                animation: glow 3s infinite alternate;
            }
            @keyframes glow { from { box-shadow: 0 0 10px #00ffcc; } to { box-shadow: 0 0 30px #00ffcc; } }
            input {
                background: rgba(255,255,255,0.1);
                border: none; outline: none; padding: 15px; margin: 10px;
                color: white; border-radius: 10px; width: 280px;
                box-shadow: inset 2px 2px 5px rgba(0,0,0,0.5);
            }
            button {
                background: #00ffcc; color: black; font-weight: bold;
                padding: 15px 40px; border: none; border-radius: 10px;
                cursor: pointer; transition: 0.3s; box-shadow: 0 5px 15px rgba(0,255,204,0.4);
            }
            button:hover { transform: scale(1.05); box-shadow: 0 0 25px #00ffcc; }
        </style>
        <div class="container">
            <h2 style="color:#00ffcc; text-shadow: 0 0 10px #00ffcc;">BLACK ADMIN</h2>
            <form method="post">
                <input type="text" name="username" placeholder="Username" required><br>
                <input type="text" name="access_key" placeholder="Password" required><br><br>
                <button type="submit">LOGIN SYSTEM</button>
            </form>
        </div>
    </body>
    '''

# ---------- [DASHBOARD - RENDER TEMPLATE] ----------
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
            shutil.rmtree(app_dir, ignore_errors=True)
            os.makedirs(app_dir, exist_ok=True)
            file.save(os.path.join(app_dir, "app.zip"))
            return redirect(url_for("index"))
    
    apps = []
    if os.path.exists(user_dir):
        for name in os.listdir(user_dir):
            app_path = os.path.join(user_dir, name)
            if os.path.isdir(app_path):
                log_file = os.path.join(app_path, "logs.txt")
                log_data = open(log_file, "r").read()[-500:] if os.path.exists(log_file) else "No logs."
                apps.append({"name": name, "running": (session['username'], name) in processes, "log": log_data})
    return render_template("index.html", apps=apps)

# ---------- [3D ADMIN LOGIN] ----------
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if session.get('is_admin'): return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        if request.form.get("u") == ADMIN_USERNAME and request.form.get("p") == ADMIN_PASSWORD:
            session.clear(); session['username'], session['is_admin'] = ADMIN_USERNAME, True
            return redirect(url_for("admin_dashboard"))
    return '''
    <body style="background:#050505; color:white; text-align:center; padding-top:100px; font-family:sans-serif;">
        <style>
            .glow-box {
                background: rgba(0, 0, 0, 0.6);
                border: 2px solid #fff;
                padding: 60px;
                border-radius: 30px;
                display: inline-block;
                animation: adminGlow 2s infinite alternate;
                transform: perspective(1000px) rotateY(10deg);
            }
            @keyframes adminGlow { from { box-shadow: 0 0 20px #ff00de; } to { box-shadow: 0 0 50px #00d4ff; } }
            input { padding: 12px; margin: 10px; width: 250px; border-radius: 8px; border: 1px solid #fff; background: transparent; color: #fff; }
            button { padding: 15px 50px; background: linear-gradient(45deg, #ff00de, #00d4ff); border: none; color: white; border-radius: 10px; cursor: pointer; font-weight: bold; }
        </style>
        <div class="glow-box">
            <h1 style="text-shadow: 0 0 15px #00d4ff;">🛡️ MASTER CONTROL</h1>
            <form method="post">
                <input type="text" name="u" placeholder="Username" required><br>
                <input type="password" name="p" placeholder="Password" required><br><br>
                <button type="submit">UNLOCK ADMIN</button>
            </form>
        </div>
    </body>
    '''

# ---------- [ADMIN DASHBOARD] ----------
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    rows = ""
    for u_name in os.listdir(UPLOAD_FOLDER):
        u_path = os.path.join(UPLOAD_FOLDER, u_name)
        if os.path.isdir(u_path):
            for a_name in os.listdir(u_path):
                if os.path.isdir(os.path.join(u_path, a_name)):
                    status = "RUNNING" if (u_name, a_name) in processes else "STOPPED"
                    rows += f"<tr><td>{u_name}</td><td>{a_name}</td><td>{status}</td><td><a href='/admin/run/{u_name}/{a_name}' style='color:lime; text-decoration:none;'>[Run]</a> | <a href='/admin/stop/{u_name}/{a_name}' style='color:orange; text-decoration:none;'>[Stop]</a> | <a href='/admin/delete/{u_name}/{a_name}' style='color:red; text-decoration:none;'>[Delete]</a> | <a href='/admin/download/{u_name}/{a_name}' style='color:cyan; text-decoration:none;'>[Download]</a></td></tr>"
    return f'''
    <body style="background:#0a0a0a; color:white; font-family:sans-serif; padding:40px;">
        <div style="background:rgba(255,255,255,0.05); padding:30px; border-radius:20px; box-shadow: 0 10px 30px rgba(0,0,0,1);">
            <h2 style="color:#00d4ff;">👑 ADMIN SUPREME PANEL</h2>
            <table border="1" style="width:100%; text-align:center; border-collapse:collapse; background:rgba(255,255,255,0.02);">
                <tr style="background:#111;"><th>User</th><th>Bot</th><th>Status</th><th>Actions</th></tr>
                {rows}
            </table>
            <br><a href="/logout" style="color:white;">Logout</a>
        </div>
    </body>
    '''

@app.route("/admin/download/<user>/<name>")
@admin_required
def admin_download(user, name):
    path = os.path.join(UPLOAD_FOLDER, user, name, "app.zip")
    if os.path.exists(path): return send_file(path, as_attachment=True)
    return "Not Found", 404

@app.route("/admin/run/<user>/<name>")
@admin_required
def admin_run(user, name): start_app(user, name); return redirect(url_for("admin_dashboard"))

@app.route("/admin/stop/<user>/<name>")
@admin_required
def admin_stop(user, name): stop_app(user, name); return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete/<user>/<name>")
@admin_required
def admin_delete(user, name):
    stop_app(user, name); shutil.rmtree(os.path.join(UPLOAD_FOLDER, user, name), ignore_errors=True)
    return redirect(url_for("admin_dashboard"))

@app.route("/run/<name>")
@login_required
def run_user(name):
    user_running = [k for k in processes.keys() if k[0] == session['username']]
    if len(user_running) >= MAX_RUNNING: stop_app(user_running[0][0], user_running[0][1])
    start_app(session['username'], name); return redirect(url_for("index"))

@app.route("/stop/<name>")
@login_required
def stop_user(name): stop_app(session['username'], name); return redirect(url_for("index"))

@app.route("/delete/<name>")
@login_required
def delete_user(name):
    stop_app(session['username'], name); shutil.rmtree(os.path.join(UPLOAD_FOLDER, session['username'], name), ignore_errors=True)
    return redirect(url_for("index"))

@app.route("/logout")
def logout(): session.clear(); return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8030)