import os
from flask import Flask, render_template, request, redirect, session
import sqlite3
import uuid
import os

app = Flask(__name__)

# Secret key
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "campus_voice_demo_secret_key"
)

# Admin Login Details
ADMIN_USERNAME = "K U AKASH"
ADMIN_PASSWORD = "AkAsH2007@."


# Database Connection
def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# Database Creation
def create_database():

    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id TEXT PRIMARY KEY,
            category TEXT,
            title TEXT,
            description TEXT,
            status TEXT
        )
    """)

    conn.commit()
    conn.close()


# Homepage
@app.route("/")
def home():
    return render_template("index.html")


# Submit Complaint
@app.route("/complaint", methods=["GET", "POST"])
def complaint():

    if request.method == "POST":

        category = request.form["category"]
        title = request.form["title"]
        description = request.form["description"]

        complaint_id = str(uuid.uuid4())[:8].upper()

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO complaints
            VALUES (?, ?, ?, ?, ?)
        """, (
            complaint_id,
            category,
            title,
            description,
            "Pending"
        ))

        conn.commit()
        conn.close()

        return render_template(
            "success.html",
            complaint_id=complaint_id
        )

    return render_template("complaint.html")


# Complaint Tracking
@app.route("/track", methods=["GET", "POST"])
def track():

    complaint = None
    error = None

    if request.method == "POST":

        complaint_id = request.form[
            "complaint_id"
        ].strip().upper()

        conn = get_db_connection()

        complaint = conn.execute(
            "SELECT * FROM complaints WHERE id = ?",
            (complaint_id,)
        ).fetchone()

        conn.close()

        if complaint is None:
            error = "Complaint ID not found! Please check again."

    return render_template(
        "track.html",
        complaint=complaint,
        error=error
    )


# Admin Login
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if (username == ADMIN_USERNAME and
                password == ADMIN_PASSWORD):

            session["admin"] = True

            return redirect("/admin")

        return render_template(
            "login.html",
            error="Invalid Username or Password!"
        )

    return render_template("login.html")


# Admin Dashboard
@app.route("/admin")
def admin():

    if not session.get("admin"):
        return redirect("/login")

    conn = get_db_connection()

    complaints = conn.execute(
        "SELECT * FROM complaints ORDER BY rowid DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        complaints=complaints
    )


# Update Complaint Status
@app.route("/update/<complaint_id>", methods=["POST"])
def update(complaint_id):

    if not session.get("admin"):
        return redirect("/login")

    status = request.form["status"]

    if status not in [
        "Pending",
        "In Progress",
        "Resolved"
    ]:
        return "Invalid status", 400

    conn = get_db_connection()

    conn.execute(
        "UPDATE complaints SET status=? WHERE id=?",
        (status, complaint_id)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")


# Delete Complaint
@app.route("/delete/<complaint_id>", methods=["POST"])
def delete(complaint_id):

    if not session.get("admin"):
        return redirect("/login")

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM complaints WHERE id=?",
        (complaint_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")


# Admin Logout
@app.route("/logout")
def logout():

    session.pop("admin", None)

    return redirect("/login")


# Create Database
create_database()


# Run Application
if __name__ == "__main__":

    app.run(debug=True)
