import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, send_from_directory

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
DB_PATH = os.path.join(BASE_DIR, 'trustvault.db')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>TrustVault | Login</title>
    <style>
        body { background-color: #0B0F0D; color: #F9FAFB; font-family: 'Segoe UI', Tahoma, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-card { background-color: #111915; border: 1px solid #26352D; border-radius: 10px; padding: 40px; width: 350px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        h2 { color: #10B981; margin-top: 0; text-align: center; }
        p.subtitle { color: #9CA3AF; font-size: 13px; text-align: center; margin-bottom: 25px; }
        label { display: block; color: #9CA3AF; font-size: 13px; margin-bottom: 6px; }
        input, select { width: 100%; padding: 10px; margin-bottom: 18px; background-color: #0B0F0D; border: 1px solid #26352D; border-radius: 6px; color: #F9FAFB; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background-color: #10B981; color: #0B0F0D; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; font-size: 15px; margin-top: 10px; }
        button:hover { background-color: #34D399; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>🛡️ TrustVault</h2>
        <p class="subtitle">Select your access role to enter vault</p>
        <form action="/login" method="POST">
            <label>Corporate Email</label>
            <input type="email" name="email" value="gopikamaddineni643@gmail.com" required>
            <label>Login As (Select Role)</label>
            <select name="role">
                <option value="Owner">👑 Owner (Full Admin & Upload Access)</option>
                <option value="Viewer">👁️ Viewer (Read-Only Access)</option>
            </select>
            <button type="submit">Authenticate & Enter</button>
        </form>
    </div>
</body>
</html>"""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>TrustVault | Security Dashboard</title>
    <style>
        body { margin: 0; font-family: 'Segoe UI', Tahoma, sans-serif; background-color: #0B0F0D; color: #F9FAFB; display: flex; height: 100vh; }
        .sidebar { width: 250px; background-color: #111915; border-right: 1px solid #26352D; padding: 20px; box-sizing: border-box; }
        .sidebar h2 { color: #10B981; font-size: 20px; margin-bottom: 30px; }
        .nav-link { display: block; color: #9CA3AF; text-decoration: none; padding: 10px 12px; margin-bottom: 8px; border-radius: 6px; font-size: 14px; }
        .nav-link.active, .nav-link:hover { background-color: rgba(16, 185, 129, 0.1); color: #10B981; }
        .main-content { flex-grow: 1; padding: 30px; overflow-y: auto; }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #26352D; padding-bottom: 15px; margin-bottom: 25px; }
        .role-badge { padding: 5px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; background-color: #10B981; color: #0B0F0D; }
        .cards-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 25px; }
        .card { background-color: #111915; border: 1px solid #26352D; border-radius: 8px; padding: 20px; }
        .card h4 { margin: 0; color: #9CA3AF; font-size: 13px; text-transform: uppercase; }
        .card .number { font-size: 30px; color: #10B981; font-weight: bold; margin: 10px 0 0 0; }
        .search-container { display: flex; gap: 10px; margin-bottom: 20px; align-items: center; }
        .search-input { flex-grow: 1; padding: 10px 15px; background-color: #111915; border: 1px solid #26352D; border-radius: 6px; color: #F9FAFB; font-size: 14px; }
        .btn-search { background-color: #111915; border: 1px solid #10B981; color: #10B981; padding: 10px 18px; border-radius: 6px; font-weight: bold; cursor: pointer; }
        .btn-upload { background-color: #10B981; color: #0B0F0D; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 14px; }
        table { width: 100%; border-collapse: collapse; background-color: #111915; border: 1px solid #26352D; border-radius: 8px; }
        th, td { padding: 14px; text-align: left; border-bottom: 1px solid #26352D; font-size: 14px; }
        th { color: #9CA3AF; background-color: #0E1411; font-size: 12px; text-transform: uppercase; }
        .badge { background-color: rgba(16, 185, 129, 0.2); color: #10B981; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        .action-link { text-decoration: none; font-size: 13px; font-weight: 600; margin-right: 12px; }
        .link-download { color: #10B981; }
        .link-delete { color: #EF4444; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>🛡️ TrustVault</h2>
        <a href="/dashboard" class="nav-link active">📊 Dashboard</a>
        <a href="/upload" class="nav-link">📤 Upload File</a>
        <hr style="border: 0; border-top: 1px solid #26352D; margin: 20px 0;">
        <a href="/" class="nav-link" style="color: #EF4444;">🚪 Logout</a>
    </div>
    <div class="main-content">
        <div class="header">
            <div>
                <h2 style="margin: 0;">Organization Security Hub</h2>
                <small style="color: #9CA3AF;">Role-Based Access Management</small>
            </div>
            <div>
                <span>{{ user_email }}</span>
                <span class="role-badge">{{ user_role }}</span>
            </div>
        </div>
        <div class="cards-grid">
            <div class="card">
                <h4>Total Documents</h4>
                <div class="number">{{ documents|length }}</div>
            </div>
            <div class="card">
                <h4>Access Level</h4>
                <div class="number" style="font-size: 20px; margin-top: 15px;">{{ user_role }}</div>
            </div>
            <div class="card">
                <h4>Security Status</h4>
                <div class="number" style="font-size: 20px; margin-top: 15px;">ENFORCED</div>
            </div>
        </div>
        <form action="/dashboard" method="GET" class="search-container">
            <input type="text" name="search" class="search-input" placeholder="🔍 Search document title or category..." value="{{ search_query }}">
            <button type="submit" class="btn-search">Filter</button>
            <a href="/dashboard" style="color: #9CA3AF; text-decoration: none; font-size: 13px;">Clear</a>
            <a href="/upload" class="btn-upload" style="margin-left: auto;">+ Upload Document</a>
        </form>
        <table>
            <thead>
                <tr>
                    <th>Document Title</th>
                    <th>Classification</th>
                    <th>Filename</th>
                    <th>Actions Allowed</th>
                </tr>
            </thead>
            <tbody>
                {% for doc in documents %}
                <tr>
                    <td><b>{{ doc.title }}</b></td>
                    <td><span class="badge">{{ doc.category }}</span></td>
                    <td>{{ doc.filename }}</td>
                    <td>
                        <a href="/download/{{ doc.filename }}" class="action-link link-download">📥 Download</a>
                        <a href="/delete/{{ doc.filename }}" class="action-link link-delete" onclick="return confirm('Delete this file?')">🗑️ Delete</a>
                    </td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="4" style="text-align: center; color: #9CA3AF; padding: 25px;">No files found. Click "+ Upload Document" to add one!</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>"""

UPLOAD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>TrustVault | Upload</title>
    <style>
        body { background-color: #0B0F0D; color: #F9FAFB; font-family: 'Segoe UI', Tahoma, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background-color: #111915; border: 1px solid #26352D; border-radius: 10px; padding: 35px; width: 380px; }
        h2 { color: #10B981; margin-top: 0; text-align: center; }
        label { display: block; color: #9CA3AF; font-size: 13px; margin-top: 15px; margin-bottom: 6px; }
        input, select { width: 100%; padding: 10px; background-color: #0B0F0D; border: 1px solid #26352D; border-radius: 6px; color: #F9FAFB; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background-color: #10B981; color: #0B0F0D; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; font-size: 15px; margin-top: 25px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🔒 Upload to Vault</h2>
        <form action="/upload" method="POST" enctype="multipart/form-data">
            <label>Document Title</label>
            <input type="text" name="title" required>
            <label>Category</label>
            <select name="category">
                <option value="Legal">Legal</option>
                <option value="Finance">Finance</option>
                <option value="HR">HR</option>
                <option value="General">General</option>
            </select>
            <label>File</label>
            <input type="file" name="file" required>
            <button type="submit">Upload File</button>
            <p style="text-align: center;"><a href="/dashboard" style="color: #9CA3AF; text-decoration: none; font-size: 13px;">Cancel</a></p>
        </form>
    </div>
</body>
</html>"""

current_user_email = "gopikamaddineni643@gmail.com"
current_user_role = "Owner"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            filename TEXT NOT NULL UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template_string(LOGIN_HTML)

@app.route("/login", methods=["POST"])
def login():
    global current_user_email, current_user_role
    email = request.form.get("email")
    role = request.form.get("role")
    if email:
        current_user_email = email
    if role:
        current_user_role = role
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    search_query = request.args.get("search", "").strip()
    conn = get_db()
    if search_query:
        cursor = conn.execute(
            "SELECT title, category, filename FROM documents WHERE title LIKE ? OR category LIKE ? ORDER BY id DESC",
            (f"%{search_query}%", f"%{search_query}%")
        )
    else:
        cursor = conn.execute("SELECT title, category, filename FROM documents ORDER BY id DESC")
    docs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template_string(DASHBOARD_HTML, 
                                  user_email=current_user_email, 
                                  user_role=current_user_role, 
                                  documents=docs,
                                  search_query=search_query)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if current_user_role != "Owner":
        return "<h2 style='color:red;'>Access Denied: Viewers cannot upload files!</h2>", 403
    if request.method == "POST":
        title = request.form.get("title")
        category = request.form.get("category")
        file = request.files.get("file")
        if file and file.filename != "":
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            conn = get_db()
            conn.execute(
                "INSERT OR REPLACE INTO documents (title, category, filename) VALUES (?, ?, ?)",
                (title, category, file.filename)
            )
            conn.commit()
            conn.close()
            return redirect(url_for("dashboard"))
    return render_template_string(UPLOAD_HTML)

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route("/delete/<filename>")
def delete_file(filename):
    if current_user_role != "Owner":
        return "<h2 style='color:red;'>Access Denied: Viewers cannot delete files!</h2>", 403
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    conn = get_db()
    conn.execute("DELETE FROM documents WHERE filename = ?", (filename,))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
