
import os
import sqlite3
import uuid

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

app = Flask(__name__)

# Render Environment Variables
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(32)

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "K U AKASH")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

DATABASE = os.environ.get("DATABASE_PATH", "database.db")

VALID_STATUSES = ["Pending", "In Progress", "Resolved"]


# Database connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Create database automatically
def create_database():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending'
        )
    """)

    conn.commit()
    conn.close()


# Home page
@app.route("/")
def home():
    return render_template("index.html")


# Submit complaint
@app.route("/complaint", methods=["GET", "POST"])
def complaint():

    if request.method == "POST":

        category = request.form.get("category", "").strip()
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()

        if not category or not title or not description:
            flash("Please fill in all fields.")
            return redirect(url_for("complaint"))

        complaint_id = str(uuid.uuid4()).replace("-", "")[:8].upper()

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO complaints
            (id, category, title, description, status)
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


# Track complaint
@app.route("/track", methods=["GET", "POST"])
def track():

    complaint_data = None
    searched = False

    if request.method == "POST":

        complaint_id = request.form.get(
            "complaint_id", ""
        ).strip().upper()

        searched = True

        conn = get_db_connection()

        complaint_data = conn.execute("""
            SELECT * FROM complaints
            WHERE id = ?
        """, (complaint_id,)).fetchone()

        conn.close()

    return render_template(
        "track.html",
        complaint=complaint_data,
        searched=searched
    )


# Admin login
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if (
            ADMIN_PASSWORD
            and username == ADMIN_USERNAME
            and password == ADMIN_PASSWORD
        ):
            session.clear()
            session["admin_logged_in"] = True

            return redirect(url_for("admin"))

        flash("Invalid username or password.")

    return render_template("login.html")


# Admin dashboard
@app.route("/admin")
def admin():

    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    conn = get_db_connection()

    complaints = conn.execute("""
        SELECT * FROM complaints
        ORDER BY rowid DESC
    """).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        complaints=complaints
    )


# Update complaint status
@app.route("/update/<complaint_id>", methods=["POST"])
def update(complaint_id):

    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    status = request.form.get("status", "")

    if status not in VALID_STATUSES:
        flash("Invalid complaint status.")
        return redirect(url_for("admin"))

    conn = get_db_connection()

    conn.execute("""
        UPDATE complaints
        SET status = ?
        WHERE id = ?
    """, (status, complaint_id))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# Delete complaint
@app.route("/delete/<complaint_id>", methods=["POST"])
def delete(complaint_id):

    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    conn = get_db_connection()

    conn.execute("""
        DELETE FROM complaints
        WHERE id = ?
    """, (complaint_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# Admin logout
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# Start application
create_database()

if __name__ == "__main__":
    app.run(debug=False)
