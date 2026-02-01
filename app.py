from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "mytube-secret"

UPLOAD_FOLDER = "videos"
THUMB_FOLDER = "thumbnails"
DB = "videos.db"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(THUMB_FOLDER, exist_ok=True)

def get_db():
    return sqlite3.connect(DB)

def init_db():
    db = get_db()
    c = db.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS videos(
        id INTEGER PRIMARY KEY,
        filename TEXT,
        title TEXT,
        description TEXT,
        thumbnail TEXT,
        user_id INTEGER,
        created TEXT
    )
    """)

    db.commit()
    db.close()

init_db()

@app.route("/")
def index():
    db = get_db()
    c = db.cursor()

    c.execute("""
    SELECT videos.*, users.username
    FROM videos
    JOIN users ON videos.user_id = users.id
    ORDER BY id DESC
    """)

    videos = c.fetchall()
    db.close()

    return render_template("index.html", videos=videos)

@app.route("/upload", methods=["GET","POST"])
def upload():

    if "user" not in session:
        return redirect("/login")

    if request.method=="POST":

        title = request.form["title"]
        desc = request.form["desc"]

        video = request.files["video"]
        thumb = request.files["thumb"]

        vname = datetime.now().strftime("%Y%m%d%H%M%S")+"_"+secure_filename(video.filename)
        tname = ""

        video.save("videos/"+vname)

        if thumb and thumb.filename!="":
            tname = datetime.now().strftime("%Y%m%d%H%M%S")+"_"+secure_filename(thumb.filename)
            thumb.save("thumbnails/"+tname)

        db = get_db()
        c = db.cursor()

        c.execute("""
        INSERT INTO videos(filename,title,description,thumbnail,user_id,created)
        VALUES(?,?,?,?,?,?)
        """,(vname,title,desc,tname,session["user"],str(datetime.now())))

        db.commit()
        db.close()

        return redirect("/")

    return render_template("upload.html")

@app.route("/videos/<f>")
def video(f):
    return send_from_directory("videos",f)

@app.route("/thumbs/<f>")
def thumb(f):
    return send_from_directory("thumbnails",f)

@app.route("/watch/<int:id>")
def watch(id):

    db = get_db()
    c = db.cursor()

    c.execute("""
    SELECT videos.*, users.username
    FROM videos
    JOIN users ON videos.user_id = users.id
    WHERE videos.id=?
    """,(id,))

    video = c.fetchone()
    db.close()

    return render_template("watch.html", video=video)

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method=="POST":

        user = request.form["username"]
        pw = generate_password_hash(request.form["password"])

        db = get_db()
        c = db.cursor()

        try:
            c.execute("INSERT INTO users(username,password) VALUES(?,?)",(user,pw))
            db.commit()
        except:
            pass

        db.close()

        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method=="POST":

        user = request.form["username"]
        pw = request.form["password"]

        db = get_db()
        c = db.cursor()

        c.execute("SELECT * FROM users WHERE username=?",(user,))
        u = c.fetchone()

        db.close()

        if u and check_password_hash(u[2],pw):
            session["user"]=u[0]
            session["name"]=u[1]
            return redirect("/")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__=="__main__":
    app.run(debug=True)
