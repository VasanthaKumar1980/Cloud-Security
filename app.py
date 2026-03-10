from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from encryption import encrypt_file, decrypt_file

app = Flask(__name__)
app.secret_key = "cloudsecret"

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# create database
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()


# LOGIN
@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        user = c.execute(
        "SELECT * FROM users WHERE username=?",(username,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user[2],password):
            session["user"] = username
            return redirect("/dashboard")

    return render_template("login.html")


# REGISTER
@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute(
        "INSERT INTO users(username,password) VALUES (?,?)",
        (username,password)
        )

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("register.html")


# DASHBOARD
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    files = os.listdir("uploads")

    return render_template("dashboard.html", files=files)


# UPLOAD FILE
@app.route("/upload", methods=["POST"])
def upload():

    if "user" not in session:
        return redirect("/")

    file = request.files["file"]

    data = file.read()

    encrypted = encrypt_file(data)

    path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)

    with open(path,"wb") as f:
        f.write(encrypted)

    return redirect("/dashboard")


# DOWNLOAD FILE
@app.route("/download/<filename>")
def download(filename):

    path = os.path.join("uploads",filename)

    with open(path,"rb") as f:
        encrypted = f.read()

    decrypted = decrypt_file(encrypted)

    temp = "temp_"+filename

    with open(temp,"wb") as f:
        f.write(decrypted)

    return send_file(temp, as_attachment=True)


# LOGOUT
@app.route("/logout")
def logout():

    session.pop("user",None)

    return redirect("/")


app.run(debug=True)