"""
app.py - Channel Broadcasting Management System
Flask application connecting to PostgreSQL database.
"""

import os
from functools import wraps

import psycopg2
from psycopg2 import extras, errors
from flask import (Flask, flash, g, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "channel_broadcasting_management_system_portal"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}


def get_db():
    if "db" not in g:
        g.db = psycopg2.connect(**DB_CONFIG)
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, args=None, one=False):
    cur = get_db().cursor(cursor_factory=extras.RealDictCursor)
    cur.execute(sql, args)
    result = cur.fetchone() if one else cur.fetchall()
    cur.close()
    return result


def execute(sql, args=None):
    db = get_db()
    cur = db.cursor()
    cur.execute(sql, args)
    db.commit()
    rowcount = cur.rowcount
    cur.close()
    return rowcount


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in as administrator.", "warning")
            return redirect(url_for("admin_login"))
        user = query("SELECT role FROM users WHERE user_id = %s",
                     (session["user_id"],), one=True)
        if not user or user["role"] != "Admin":
            flash("Administrator access required.", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function


# ==================== PUBLIC ROUTES ====================

@app.route("/")
def index():
    stats = query(
        "SELECT "
        "(SELECT COUNT(*) FROM shows) AS total_shows, "
        "(SELECT COUNT(*) FROM users) AS total_users, "
        "(SELECT COUNT(*) FROM channels) AS total_channels, "
        "(SELECT COUNT(*) FROM schedules) AS total_schedules, "
        "(SELECT COUNT(*) FROM schedules WHERE status = 'Cancelled') AS cancelled",
        one=True,
    )
    return render_template("index.html", stats=stats)


@app.route("/shows")
def shows():
    shows_list = query(
        "SELECT s.show_id, s.title, s.description, s.duration_minutes, "
        "a.agency_name, g.genre_name "
        "FROM shows s "
        "JOIN agencies a ON s.agency_id = a.agency_id "
        "JOIN genres g ON s.genre_id = g.genre_id "
        "ORDER BY s.created_at DESC"
    )
    return render_template("shows.html", shows=shows_list)


@app.route("/schedule")
def schedule():
    schedules = query(
        "SELECT * FROM broadcast_schedule_view "
        "ORDER BY broadcast_date, start_time"
    )
    return render_template("schedule.html", schedules=schedules)


# ==================== AUTH ROUTES ====================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not full_name or not email or not password:
            flash("All fields are required.", "danger")
        elif password != confirm:
            flash("Passwords do not match.", "danger")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
        else:
            existing = query("SELECT user_id FROM users WHERE email = %s",
                             (email,), one=True)
            if existing:
                flash("Email already registered.", "danger")
            else:
                password_hash = generate_password_hash(password)
                execute(
                    "INSERT INTO users (full_name, email, password_hash, role) "
                    "VALUES (%s, %s, %s, 'User')",
                    (full_name, email, password_hash),
                )
                flash("Registration successful. Please log in.", "success")
                return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        user = query("SELECT * FROM users WHERE email = %s", (email,), one=True)
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["user_id"]
            session["full_name"] = user["full_name"]
            session["role"] = user["role"]
            if user["role"] == "Admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("index"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


# ==================== USER ROUTES ====================

@app.route("/add-show", methods=["GET", "POST"])
@login_required
def add_show():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        agency_id = request.form.get("agency_id")
        genre_id = request.form.get("genre_id")
        duration = request.form.get("duration_minutes")

        if not all([title, description, agency_id, genre_id, duration]):
            flash("All fields are required.", "danger")
        else:
            try:
                execute(
                    "INSERT INTO shows "
                    "(title, description, agency_id, genre_id, "
                    "duration_minutes, created_by) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (title, description, agency_id, genre_id,
                     duration, session["user_id"]),
                )
                flash("Show submitted successfully!", "success")
                return redirect(url_for("index"))
            except psycopg2.Error:
                flash("Error submitting show. Check your inputs.", "danger")

    agencies = query("SELECT agency_id, agency_name FROM agencies ORDER BY agency_name")
    genres = query("SELECT genre_id, genre_name FROM genres ORDER BY genre_name")
    return render_template("add_show.html", agencies=agencies, genres=genres)


# ==================== ADMIN ROUTES ====================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        user = query("SELECT * FROM users WHERE email = %s AND role = %s",
                     (email, "Admin"), one=True)
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["user_id"]
            session["full_name"] = user["full_name"]
            session["role"] = "Admin"
            flash("Welcome, Administrator!", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Invalid administrator credentials.", "danger")
    return render_template("login.html", admin=True)


@app.route("/admin")
@admin_required
def admin_dashboard():
    users = query("SELECT * FROM users ORDER BY created_at DESC")
    agencies = query("SELECT * FROM agencies ORDER BY agency_name")
    channels = query("SELECT * FROM channels ORDER BY channel_name")
    shows_list = query(
        "SELECT s.*, a.agency_name, g.genre_name "
        "FROM shows s "
        "JOIN agencies a ON s.agency_id = a.agency_id "
        "JOIN genres g ON s.genre_id = g.genre_id "
        "ORDER BY s.created_at DESC"
    )
    schedules = query(
        "SELECT * FROM broadcast_schedule_view ORDER BY broadcast_date"
    )
    return render_template("admin.html",
                           users=users, agencies=agencies,
                           channels=channels, shows=shows_list,
                           schedules=schedules)


@app.route("/admin/schedule", methods=["GET", "POST"])
@admin_required
def admin_schedule():
    if request.method == "POST":
        show_id = request.form.get("show_id")
        channel_id = request.form.get("channel_id")
        broadcast_date = request.form.get("broadcast_date")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")

        if end_time <= start_time:
            flash("End time must be after start time.", "danger")
        else:
            try:
                execute(
                    "INSERT INTO schedules "
                    "(show_id, channel_id, broadcast_date, start_time, end_time) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (show_id, channel_id, broadcast_date, start_time, end_time),
                )
                flash("Schedule created successfully!", "success")
                return redirect(url_for("admin_schedule"))
            except errors.ExclusionViolation:
                flash("Schedule conflict: overlapping time on this channel.", "danger")
            except psycopg2.Error as e:
                flash(f"Error creating schedule: {e}", "danger")

    all_shows = query("SELECT show_id, title FROM shows ORDER BY title")
    all_channels = query("SELECT channel_id, channel_name FROM channels ORDER BY channel_name")
    current_schedules = query(
        "SELECT * FROM broadcast_schedule_view ORDER BY broadcast_date, start_time"
    )
    return render_template("admin.html", schedule_mode=True,
                           all_shows=all_shows, all_channels=all_channels,
                           schedules=current_schedules)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
