import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory

app = Flask(__name__)

BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
DB_PATH = os.path.join(BASE_DIR, 'trustvault.db')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

current_user_email = "gopikamaddineni643@gmail.com"
current_user_role = "Owner"

# Database Connection Helper
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Database Tables Create Chese Function
def init_db():
    conn = get_db()
    # Documents Table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            filename TEXT NOT NULL UNIQUE
        )
    ''')
    # Audit Logs Table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT NOT NULL,
            user TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Start avvagane Database create chesthundi
init_db()

def log_event(action, details, status="SUCCESS"):
    conn = get_db()
    conn.execute(
        "INSERT INTO audit_logs (time, user, action, details, status) VALUES (?, ?, ?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), current_user_email, action, details, status)
    )
    conn.commit()
    conn.close()

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    global current_user_email, current_user_role
    email = request.form.get("email")
    role = request.form.get("role")
    if email:
        current_user_email = email
    if role:
        current_user_role = role

    log_event("USER_LOGIN", f"Logged in as {current_user_role}")
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    search_query = request.args.get("search", "").strip()
    conn = get_db()
    
    # SQLite Database nundi search & fetch chesthundi
    if search_query:
        cursor = conn.execute(
            "SELECT title, category, filename FROM documents WHERE title LIKE ? OR category LIKE ? ORDER BY id DESC",
            (f"%{search_query}%", f"%{search_query}%")
        )
    else:
        cursor = conn.execute("SELECT title, category, filename FROM documents ORDER BY id DESC")
        
    docs = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return render_template("dashboard.html", 
                           user_email=current_user_email, 
                           user_role=current_user_role, 
                           documents=docs,
                           search_query=search_query)

@app.route("/logs")
def view_logs():
    conn = get_db()
    cursor = conn.execute("SELECT time, user, action, details, status FROM audit_logs ORDER BY id DESC")
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template("logs.html", logs=logs)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if current_user_role != "Owner":
        log_event("UNAUTHORIZED_UPLOAD", "Viewer attempted file upload", status="BLOCKED")
        return "<h2 style='color:red;'>Access Denied: Viewers cannot upload files!</h2>", 403

    if request.method == "POST":
        title = request.form.get("title")
        category = request.form.get("category")
        file = request.files.get("file")

        if file and file.filename != "":
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            # SQLite Database lo save chesthunnam!
            conn = get_db()
            conn.execute(
                "INSERT OR REPLACE INTO documents (title, category, filename) VALUES (?, ?, ?)",
                (title, category, file.filename)
            )
            conn.commit()
            conn.close()

            log_event("DOCUMENT_UPLOAD", f"Uploaded: {file.filename} ({category})")
            return redirect(url_for("dashboard"))

    return render_template("upload.html")

@app.route("/download/<filename>")
def download_file(filename):
    log_event("DOCUMENT_DOWNLOAD", f"Downloaded: {filename}")
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route("/delete/<filename>")
def delete_file(filename):
    if current_user_role != "Owner":
        log_event("UNAUTHORIZED_DELETE", f"Viewer attempted deleting {filename}", status="BLOCKED")
        return "<h2 style='color:red;'>Access Denied: Viewers cannot delete files!</h2>", 403

    # Delete physical file from folder
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    # Delete record from SQLite Database!
    conn = get_db()
    conn.execute("DELETE FROM documents WHERE filename = ?", (filename,))
    conn.commit()
    conn.close()

    log_event("DOCUMENT_DELETE", f"Deleted: {filename}")
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)