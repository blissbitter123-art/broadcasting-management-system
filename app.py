"""
app.py
------
Channel Broadcasting Management System - Flask application.

Routes
------
Public : /  |  /shows  |  /shows/<show_id>
Auth   : /register  |  /login  |  /logout  |  /admin/login  |  /admin/logout
User   : /dashboard  |  /shows/add  |  /my-shows  |  /shows/edit/<id>  |  /shows/delete/<id>
Admin  : /admin/dashboard  |  /admin/shows  |  /admin/shows/<id>/approve|reject|delete
         /admin/users  |  /admin/users/<id>  |  /admin/users/<id>/toggle-status
"""

import logging
import os
import re
from datetime import date, datetime
from functools import wraps

import psycopg2
from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_wtf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash

from database import DatabaseError, execute, fetch_all, fetch_one, transaction

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY") or os.urandom(32).hex(),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true",
    REMEMBER_COOKIE_HTTPONLY=True,
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,  # 2 MB form limit
    WTF_CSRF_TIME_LIMIT=None,
)

csrf = CSRFProtect(app)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

CATEGORIES = [
    "News", "Entertainment", "Sports", "Drama", "Music", "Documentary",
    "Kids", "Talk Show", "Religious", "Business", "Education", "Other",
]

LANGUAGES = [
    "English", "Hindi", "Tamil", "Telugu", "Malayalam", "Kannada",
    "Bengali", "Marathi", "Gujarati", "Urdu", "Other",
]

STATUSES = ["Pending", "Approved", "Rejected"]

SHOW_SORTS = {
    "date_asc": "broadcast_date ASC, start_time ASC",
    "date_desc": "broadcast_date DESC, start_time DESC",
    "title": "title ASC",
    "submitted": "submitted_at DESC",
}

FIELD_LIMITS = {
    "title": 200,
    "description": 2000,
    "category": 80,
    "agency_name": 120,
    "host_name": 120,
    "channel_name": 120,
    "language": 40,
    "target_audience": 120,
    "poster_url": 500,
    "additional_notes": 2000,
}


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def parse_time(value):
    """Parse an HTML time value (HH:MM or HH:MM:SS) into datetime.time."""
    value = (value or "").strip()
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue
    return None


def minutes_between(start, end):
    if not start or not end:
        return None
    return int((datetime.combine(date.today(), end) - datetime.combine(date.today(), start)).total_seconds() // 60)


def with_duration(rows):
    for row in rows:
        row["duration_minutes"] = minutes_between(row.get("start_time"), row.get("end_time"))
    return rows


def overlap_clause_params(channel_name, broadcast_date, start_time, end_time, exclude_show_id=None):
    """Shared SQL fragment: approved shows on the same channel that overlap."""
    sql = """
        SELECT show_id, title, start_time, end_time
        FROM shows
        WHERE status = 'Approved'
          AND LOWER(channel_name) = LOWER(%s)
          AND broadcast_date = %s
          AND start_time < %s
          AND end_time > %s
    """
    params = [channel_name, broadcast_date, end_time, start_time]
    if exclude_show_id:
        sql += " AND show_id <> %s"
        params.append(exclude_show_id)
    return sql, params


def find_conflicts(channel_name, broadcast_date, start_time, end_time, exclude_show_id=None):
    """Return approved shows that overlap the given schedule on the same channel."""
    query, params = overlap_clause_params(
        channel_name, broadcast_date, start_time, end_time, exclude_show_id
    )
    return fetch_all(query, params)


def load_approved_overlaps():
    """All approved shows, grouped for fast conflict checks on the admin pages."""
    rows = fetch_all(
        "SELECT show_id, title, channel_name, broadcast_date, start_time, end_time "
        "FROM shows WHERE status = 'Approved'"
    )
    grouped = {}
    for row in rows:
        grouped.setdefault((row["channel_name"].strip().lower(), row["broadcast_date"]), []).append(row)
    return grouped


def conflicts_for(show, grouped):
    key = (str(show["channel_name"]).strip().lower(), show["broadcast_date"])
    result = []
    for other in grouped.get(key, []):
        if other["show_id"] == show["show_id"]:
            continue
        if other["start_time"] < show["end_time"] and other["end_time"] > show["start_time"]:
            result.append(other)
    return result


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_show_form(form):
    """Server-side validation for the add / edit show forms."""
    errors = {}
    data = {}

    def clean(key, limit, label, required=True):
        value = (form.get(key) or "").strip()
        if len(value) > limit:
            errors[key] = "%s must be %d characters or fewer." % (label, limit)
            value = value[:limit]
        if required and not value:
            errors[key] = "%s is required." % label
        data[key] = value

    clean("title", FIELD_LIMITS["title"], "Show title")
    clean("description", FIELD_LIMITS["description"], "Description")
    clean("category", FIELD_LIMITS["category"], "Category")
    clean("agency_name", FIELD_LIMITS["agency_name"], "Agency name")
    clean("host_name", FIELD_LIMITS["host_name"], "Host name")
    clean("channel_name", FIELD_LIMITS["channel_name"], "Channel")
    clean("language", FIELD_LIMITS["language"], "Language")
    clean("target_audience", FIELD_LIMITS["target_audience"], "Target audience", required=False)
    clean("poster_url", FIELD_LIMITS["poster_url"], "Poster URL", required=False)
    clean("additional_notes", FIELD_LIMITS["additional_notes"], "Notes", required=False)

    if data.get("category") and data["category"] not in CATEGORIES:
        errors["category"] = "Please choose a category from the list."

    # --- broadcast date ----------------------------------------------------
    raw_date = (form.get("broadcast_date") or "").strip()
    data["broadcast_date"] = None
    if not raw_date:
        errors["broadcast_date"] = "Broadcast date is required."
    else:
        try:
            data["broadcast_date"] = date.fromisoformat(raw_date)
        except ValueError:
            errors["broadcast_date"] = "Enter a valid date in YYYY-MM-DD format."
    if data["broadcast_date"] and data["broadcast_date"] < date.today():
        errors["broadcast_date"] = "Broadcast date cannot be in the past."

    # --- start / end time --------------------------------------------------
    raw_start = (form.get("start_time") or "").strip()
    raw_end = (form.get("end_time") or "").strip()
    data["start_time"] = parse_time(raw_start) if raw_start else None
    data["end_time"] = parse_time(raw_end) if raw_end else None

    if not raw_start:
        errors["start_time"] = "Start time is required."
    elif data["start_time"] is None:
        errors["start_time"] = "Enter a valid start time (HH:MM)."

    if not raw_end:
        errors["end_time"] = "End time is required."
    elif data["end_time"] is None:
        errors["end_time"] = "Enter a valid end time (HH:MM)."

    if data["start_time"] and data["end_time"] and data["end_time"] <= data["start_time"]:
        errors["end_time"] = "End time must be later than the start time."

    # --- optional poster URL ----------------------------------------------
    if data["poster_url"] and not data["poster_url"].lower().startswith(("http://", "https://")):
        errors["poster_url"] = "Poster URL must start with http:// or https://"

    data["duration_minutes"] = minutes_between(data.get("start_time"), data.get("end_time"))
    return data, errors


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------

@app.before_request
def load_current_user():
    g.user = None
    user_id = session.get("user_id")
    if user_id and not request.path.startswith("/static"):
        g.user = fetch_one(
            "SELECT user_id, full_name, agency_name, email, role, is_active "
            "FROM users WHERE user_id = %s",
            (user_id,),
        )
        if g.user is None:
            session.clear()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            flash("Please log in to access that page.", "warning")
            return redirect(url_for("login"))
        if not g.user["is_active"]:
            session.clear()
            flash("Your account has been deactivated. Contact the administrator.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            flash("Please sign in to the administrator portal.", "warning")
            return redirect(url_for("admin_login"))
        if g.user["role"] != "admin":
            flash("Administrator access is required for that page.", "error")
            return redirect(url_for("dashboard"))
        if not g.user["is_active"]:
            session.clear()
            flash("Your administrator account is deactivated.", "error")
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)

    return wrapped


def get_show_or_404(show_id):
    show = fetch_one("SELECT * FROM shows WHERE show_id = %s", (show_id,))
    if show is None:
        abort(404)
    return show


def owned_show_or_404(show_id):
    show = get_show_or_404(show_id)
    if show["user_id"] != g.user["user_id"]:
        abort(403)
    return show


# ---------------------------------------------------------------------------
# Template helpers
# ---------------------------------------------------------------------------

@app.template_filter("fmt_date")
def fmt_date(value):
    return value.strftime("%d %b %Y") if value else "-"


@app.template_filter("fmt_time")
def fmt_time(value):
    return value.strftime("%H:%M") if value else "-"


@app.template_filter("fmt_datetime")
def fmt_datetime(value):
    return value.strftime("%d %b %Y, %H:%M") if value else "-"


@app.template_filter("fmt_duration")
def fmt_duration(minutes):
    if minutes is None:
        return "-"
    minutes = int(minutes)
    return "%dh %02dm" % (minutes // 60, minutes % 60)


@app.context_processor
def inject_globals():
    return {"CATEGORIES": CATEGORIES, "LANGUAGES": LANGUAGES, "STATUSES": STATUSES}


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    try:
        upcoming = with_duration(fetch_all(
            "SELECT * FROM shows WHERE status = 'Approved' AND broadcast_date >= CURRENT_DATE "
            "ORDER BY broadcast_date ASC, start_time ASC LIMIT 6"
        ))
        counters = fetch_one(
            "SELECT (SELECT COUNT(*) FROM users) AS users, "
            "(SELECT COUNT(*) FROM shows WHERE status = 'Approved') AS approved, "
            "(SELECT COUNT(DISTINCT channel_name) FROM shows WHERE status = 'Approved') AS channels"
        )
    except DatabaseError as exc:
        flash(str(exc), "error")
        upcoming, counters = [], {"users": 0, "approved": 0, "channels": 0}
    return render_template("index.html", shows=upcoming, counters=counters)


@app.route("/shows")
def public_shows():
    q = (request.args.get("q") or "").strip()
    category = (request.args.get("category") or "").strip()
    channel = (request.args.get("channel") or "").strip()
    filter_date = (request.args.get("filter_date") or "").strip()
    sort = request.args.get("sort") or "date_asc"
    if sort not in SHOW_SORTS:
        sort = "date_asc"

    clauses = ["s.status = 'Approved'"]
    params = []

    if q:
        clauses.append("s.title ILIKE %s")
        params.append("%" + q + "%")
    if category:
        clauses.append("s.category = %s")
        params.append(category)
    if channel:
        clauses.append("s.channel_name = %s")
        params.append(channel)
    if filter_date:
        try:
            clauses.append("s.broadcast_date = %s")
            params.append(date.fromisoformat(filter_date))
        except ValueError:
            flash("Ignored invalid date filter.", "warning")

    query = (
        "SELECT s.*, u.full_name AS owner_name FROM shows s "
        "JOIN users u ON u.user_id = s.user_id WHERE " + " AND ".join(clauses) +
        " ORDER BY " + SHOW_SORTS[sort]
    )

    try:
        shows = with_duration(fetch_all(query, params))
        channels = [row["channel_name"] for row in fetch_all(
            "SELECT DISTINCT channel_name FROM shows WHERE status = 'Approved' ORDER BY channel_name"
        )]
    except DatabaseError as exc:
        flash(str(exc), "error")
        shows, channels = [], []

    return render_template(
        "shows.html",
        shows=shows,
        channels=channels,
        q=q,
        category=category,
        channel=channel,
        filter_date=filter_date,
        sort=sort,
    )


@app.route("/shows/<int:show_id>")
def show_details(show_id):
    show = get_show_or_404(show_id)
    is_owner = bool(g.user and g.user["user_id"] == show["user_id"])
    is_admin = bool(g.user and g.user["role"] == "admin")

    if show["status"] != "Approved" and not (is_owner or is_admin):
        abort(404)

    owner = fetch_one("SELECT full_name, agency_name, email, phone FROM users WHERE user_id = %s",
                      (show["user_id"],))
    history = []
    if is_owner or is_admin:
        history = fetch_all(
            "SELECT h.*, a.full_name AS admin_name FROM show_status_history h "
            "LEFT JOIN users a ON a.user_id = h.admin_id "
            "WHERE h.show_id = %s ORDER BY h.changed_at DESC",
            (show_id,),
        )
    with_duration([show])
    return render_template(
        "show_details.html", show=show, owner=owner, history=history,
        is_owner=is_owner, is_admin=is_admin,
    )


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("dashboard"))

    errors, form_data = {}, {}

    if request.method == "POST":
        form_data = {key: (request.form.get(key) or "").strip()
                     for key in ("full_name", "agency_name", "email", "phone", "password", "confirm_password")}
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""

        if not form_data["full_name"]:
            errors["full_name"] = "Full name is required."
        elif len(form_data["full_name"]) > 100:
            errors["full_name"] = "Full name must be 100 characters or fewer."

        if not form_data["agency_name"]:
            errors["agency_name"] = "Agency or organization name is required."
        elif len(form_data["agency_name"]) > 120:
            errors["agency_name"] = "Agency name must be 120 characters or fewer."

        if not form_data["email"]:
            errors["email"] = "Email address is required."
        elif not EMAIL_RE.match(form_data["email"]):
            errors["email"] = "Enter a valid email address."
        elif len(form_data["email"]) > 120:
            errors["email"] = "Email address is too long."

        if not form_data["phone"]:
            errors["phone"] = "Phone number is required."
        elif len(form_data["phone"]) > 20:
            errors["phone"] = "Phone number must be 20 characters or fewer."

        if not password:
            errors["password"] = "Password is required."
        elif len(password) < 6:
            errors["password"] = "Password must be at least 6 characters."
        elif len(password) > 200:
            errors["password"] = "Password is too long."

        if not confirm:
            errors["confirm_password"] = "Please confirm your password."
        elif password != confirm:
            errors["confirm_password"] = "Passwords do not match."

        if not errors:
            existing = fetch_one("SELECT user_id FROM users WHERE LOWER(email) = LOWER(%s)",
                                 (form_data["email"],))
            if existing:
                errors["email"] = "An account with this email already exists."
            else:
                try:
                    # role is always 'user' - never taken from user input
                    execute(
                        "INSERT INTO users (full_name, agency_name, email, phone, password_hash, role) "
                        "VALUES (%s, %s, %s, %s, %s, 'user')",
                        (
                            form_data["full_name"], form_data["agency_name"],
                            form_data["email"].lower(), form_data["phone"],
                            generate_password_hash(password),
                        ),
                    )
                    flash("Registration successful. Please log in with your account.", "success")
                    return redirect(url_for("login"))
                except DatabaseError as exc:
                    errors["email"] = str(exc)

        if errors:
            flash("Please fix the highlighted errors.", "error")

    return render_template("register.html", errors=errors, form=form_data)


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("admin_dashboard" if g.user["role"] == "admin" else "dashboard"))

    errors, form_data = {}, {}

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        form_data = {"email": email}

        if not email:
            errors["email"] = "Email address is required."
        if not password:
            errors["password"] = "Password is required."

        if not errors:
            user = fetch_one("SELECT * FROM users WHERE LOWER(email) = LOWER(%s)", (email,))
            if user is None or not check_password_hash(user["password_hash"], password):
                errors["form"] = "Invalid email or password."
            elif user["role"] != "user":
                errors["form"] = "This is an administrator account. Use the admin portal."
            elif not user["is_active"]:
                errors["form"] = "Your account has been deactivated. Contact the administrator."
            else:
                session.clear()
                session["user_id"] = user["user_id"]
                session["role"] = user["role"]
                session["full_name"] = user["full_name"]
                flash("Welcome back, %s!" % user["full_name"], "success")
                return redirect(url_for("dashboard"))

        if errors:
            flash("Please fix the highlighted errors.", "error")

    return render_template("login.html", errors=errors, form=form_data)


@app.route("/logout", methods=["POST"])
@app.route("/admin/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if g.user and g.user["role"] == "admin" and g.user["is_active"]:
        return redirect(url_for("admin_dashboard"))

    errors, form_data = {}, {}

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        form_data = {"email": email}

        if not email:
            errors["email"] = "Email address is required."
        if not password:
            errors["password"] = "Password is required."

        if not errors:
            user = fetch_one("SELECT * FROM users WHERE LOWER(email) = LOWER(%s)", (email,))
            if user is None or not check_password_hash(user["password_hash"], password):
                errors["form"] = "Invalid administrator email or password."
            elif user["role"] != "admin":
                errors["form"] = "This account is not an administrator account."
            elif not user["is_active"]:
                errors["form"] = "This administrator account is deactivated."
            else:
                session.clear()
                session["user_id"] = user["user_id"]
                session["role"] = user["role"]
                session["full_name"] = user["full_name"]
                flash("Administrator session started.", "success")
                return redirect(url_for("admin_dashboard"))

        if errors:
            flash("Please fix the highlighted errors.", "error")

    return render_template("admin_login.html", errors=errors, form=form_data)


# ---------------------------------------------------------------------------
# User dashboard and show management
# ---------------------------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():
    try:
        stats = fetch_one(
            "SELECT COUNT(*) AS total, "
            "COUNT(*) FILTER (WHERE status = 'Approved') AS approved, "
            "COUNT(*) FILTER (WHERE status = 'Pending') AS pending, "
            "COUNT(*) FILTER (WHERE status = 'Rejected') AS rejected "
            "FROM shows WHERE user_id = %s",
            (g.user["user_id"],),
        )
        recent = with_duration(fetch_all(
            "SELECT * FROM shows WHERE user_id = %s ORDER BY submitted_at DESC LIMIT 5",
            (g.user["user_id"],),
        ))
        upcoming = with_duration(fetch_all(
            "SELECT * FROM shows WHERE user_id = %s AND status = 'Approved' "
            "AND broadcast_date >= CURRENT_DATE "
            "ORDER BY broadcast_date ASC, start_time ASC LIMIT 5",
            (g.user["user_id"],),
        ))
    except DatabaseError as exc:
        flash(str(exc), "error")
        stats, recent, upcoming = {"total": 0, "approved": 0, "pending": 0, "rejected": 0}, [], []

    return render_template("dashboard.html", stats=stats, recent=recent, upcoming=upcoming)


@app.route("/shows/add", methods=["GET", "POST"])
@login_required
def add_show():
    errors, data = {}, {}

    if request.method == "POST":
        data, errors = validate_show_form(request.form)

        conflicts = []
        if not errors:
            conflicts = find_conflicts(
                data["channel_name"], data["broadcast_date"],
                data["start_time"], data["end_time"],
            )

        if errors:
            flash("Please fix the highlighted errors.", "error")
        else:
            try:
                execute(
                    """
                    INSERT INTO shows (user_id, title, description, category, agency_name,
                                       host_name, channel_name, broadcast_date, start_time,
                                       end_time, language, target_audience, poster_url,
                                       additional_notes, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pending')
                    """,
                    (
                        g.user["user_id"], data["title"], data["description"], data["category"],
                        data["agency_name"], data["host_name"], data["channel_name"],
                        data["broadcast_date"], data["start_time"], data["end_time"],
                        data["language"], data["target_audience"] or None,
                        data["poster_url"] or None, data["additional_notes"] or None,
                    ),
                )
                flash("Show submitted successfully. It is now pending administrator approval.", "success")
                if conflicts:
                    names = ", ".join(c["title"] for c in conflicts[:3])
                    flash(
                        "Schedule warning: this slot overlaps with approved show(s): %s. "
                        "An administrator will review the conflict." % names,
                        "warning",
                    )
                return redirect(url_for("my_shows"))
            except DatabaseError as exc:
                flash(str(exc), "error")

    if not data:
        data = {
            "agency_name": g.user["agency_name"],
            "broadcast_date": "",
            "start_time": "",
            "end_time": "",
        }

    return render_template("add_show.html", errors=errors, show=data,
                           duration=data.get("duration_minutes"))


@app.route("/my-shows")
@login_required
def my_shows():
    q = (request.args.get("q") or "").strip()
    status = (request.args.get("status") or "").strip()
    sort = request.args.get("sort") or "date_asc"
    if sort not in SHOW_SORTS:
        sort = "date_asc"

    clauses = ["user_id = %s"]
    params = [g.user["user_id"]]

    if q:
        clauses.append("title ILIKE %s")
        params.append("%" + q + "%")
    if status in STATUSES:
        clauses.append("status = %s")
        params.append(status)

    query = ("SELECT * FROM shows WHERE " + " AND ".join(clauses) +
             " ORDER BY " + SHOW_SORTS[sort])

    try:
        shows = with_duration(fetch_all(query, params))
    except DatabaseError as exc:
        flash(str(exc), "error")
        shows = []

    return render_template("my_shows.html", shows=shows, q=q, status=status, sort=sort)


@app.route("/shows/edit/<int:show_id>", methods=["GET", "POST"])
@login_required
def edit_show(show_id):
    show = owned_show_or_404(show_id)
    was_approved = show["status"] == "Approved"
    errors, data = {}, dict(show)

    if request.method == "POST":
        data, errors = validate_show_form(request.form)

        conflicts = []
        if not errors:
            conflicts = find_conflicts(
                data["channel_name"], data["broadcast_date"],
                data["start_time"], data["end_time"],
                exclude_show_id=show_id,
            )

        if errors:
            flash("Please fix the highlighted errors.", "error")
        else:
            try:
                new_status = "Pending" if was_approved else show["status"]
                new_reason = None if was_approved else show["rejection_reason"]
                execute(
                    """
                    UPDATE shows SET title=%s, description=%s, category=%s, agency_name=%s,
                        host_name=%s, channel_name=%s, broadcast_date=%s, start_time=%s,
                        end_time=%s, language=%s, target_audience=%s, poster_url=%s,
                        additional_notes=%s, status=%s, rejection_reason=%s,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE show_id = %s AND user_id = %s
                    """,
                    (
                        data["title"], data["description"], data["category"], data["agency_name"],
                        data["host_name"], data["channel_name"], data["broadcast_date"],
                        data["start_time"], data["end_time"], data["language"],
                        data["target_audience"] or None, data["poster_url"] or None,
                        data["additional_notes"] or None, new_status, new_reason,
                        show_id, g.user["user_id"],
                    ),
                )
                if was_approved:
                    flash("Show updated. Because it was approved, it is now Pending re-approval.", "warning")
                else:
                    flash("Show updated successfully.", "success")
                if conflicts:
                    names = ", ".join(c["title"] for c in conflicts[:3])
                    flash("Schedule warning: overlaps with approved show(s): %s." % names, "warning")
                return redirect(url_for("my_shows"))
            except DatabaseError as exc:
                flash(str(exc), "error")

    with_duration([data])
    return render_template("edit_show.html", errors=errors, show=data,
                           was_approved=was_approved, duration=data.get("duration_minutes"))


@app.route("/shows/delete/<int:show_id>", methods=["POST"])
@login_required
def delete_show(show_id):
    owned_show_or_404(show_id)
    try:
        execute("DELETE FROM shows WHERE show_id = %s AND user_id = %s",
                (show_id, g.user["user_id"]))
        flash("Show deleted successfully.", "success")
    except DatabaseError as exc:
        flash(str(exc), "error")
    return redirect(url_for("my_shows"))


# ---------------------------------------------------------------------------
# Administrator portal
# ---------------------------------------------------------------------------

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    try:
        stats = fetch_one(
            "SELECT "
            "(SELECT COUNT(*) FROM users) AS total_users, "
            "(SELECT COUNT(DISTINCT agency_name) FROM users) AS total_agencies, "
            "(SELECT COUNT(*) FROM shows) AS total_shows, "
            "COUNT(*) FILTER (WHERE status = 'Approved') AS approved, "
            "COUNT(*) FILTER (WHERE status = 'Pending') AS pending, "
            "COUNT(*) FILTER (WHERE status = 'Rejected') AS rejected, "
            "COUNT(*) FILTER (WHERE status = 'Approved' AND broadcast_date >= CURRENT_DATE) AS upcoming "
            "FROM shows"
        )
        recent = with_duration(fetch_all(
            "SELECT s.show_id, s.title, s.agency_name, s.channel_name, s.broadcast_date, "
            "s.start_time, s.end_time, s.status, s.submitted_at, u.full_name AS owner_name "
            "FROM shows s JOIN users u ON u.user_id = s.user_id "
            "ORDER BY s.submitted_at DESC LIMIT 10"
        ))
    except DatabaseError as exc:
        flash(str(exc), "error")
        stats, recent = None, []

    return render_template("admin_dashboard.html", stats=stats, recent=recent)


@app.route("/admin/shows")
@admin_required
def admin_shows():
    q = (request.args.get("q") or "").strip()
    agency = (request.args.get("agency") or "").strip()
    status = (request.args.get("status") or "").strip()
    channel = (request.args.get("channel") or "").strip()
    filter_date = (request.args.get("filter_date") or "").strip()
    sort = request.args.get("sort") or "date_asc"
    if sort not in SHOW_SORTS:
        sort = "date_asc"

    clauses = ["1 = 1"]
    params = []

    if q:
        clauses.append("s.title ILIKE %s")
        params.append("%" + q + "%")
    if agency:
        clauses.append("s.agency_name ILIKE %s")
        params.append("%" + agency + "%")
    if status in STATUSES:
        clauses.append("s.status = %s")
        params.append(status)
    if channel:
        clauses.append("s.channel_name = %s")
        params.append(channel)
    if filter_date:
        try:
            clauses.append("s.broadcast_date = %s")
            params.append(date.fromisoformat(filter_date))
        except ValueError:
            flash("Ignored invalid date filter.", "warning")

    query = (
        "SELECT s.*, u.full_name AS owner_name, u.email AS owner_email, "
        "u.phone AS owner_phone FROM shows s "
        "JOIN users u ON u.user_id = s.user_id WHERE " + " AND ".join(clauses) +
        " ORDER BY " + SHOW_SORTS[sort]
    )

    try:
        shows = with_duration(fetch_all(query, params))
        grouped = load_approved_overlaps()
        channels = [row["channel_name"] for row in fetch_all(
            "SELECT DISTINCT channel_name FROM shows ORDER BY channel_name"
        )]
        agencies = [row["agency_name"] for row in fetch_all(
            "SELECT DISTINCT agency_name FROM shows ORDER BY agency_name"
        )]
    except DatabaseError as exc:
        flash(str(exc), "error")
        shows, grouped, channels, agencies = [], {}, [], []

    for show in shows:
        show["conflicts"] = conflicts_for(show, grouped)

    return render_template(
        "admin_shows.html", shows=shows, channels=channels, agencies=agencies,
        q=q, agency=agency, status=status, channel=channel,
        filter_date=filter_date, sort=sort,
    )


@app.route("/admin/shows/<int:show_id>/approve", methods=["POST"])
@admin_required
def admin_approve_show(show_id):
    show = get_show_or_404(show_id)

    conflicts = find_conflicts(
        show["channel_name"], show["broadcast_date"],
        show["start_time"], show["end_time"], exclude_show_id=show_id,
    )
    if conflicts:
        names = "; ".join(
            "'%s' (ID %s, %s to %s)" % (
                c["title"], c["show_id"],
                c["start_time"].strftime("%H:%M"), c["end_time"].strftime("%H:%M"),
            ) for c in conflicts
        )
        flash(
            "Cannot approve: schedule conflict on channel '%s' with %s. "
            "Resolve the overlap first." % (show["channel_name"], names),
            "error",
        )
        return redirect(url_for("admin_shows") + "#show-%d" % show_id)

    try:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE shows SET status = 'Approved', rejection_reason = NULL, "
                    "updated_at = CURRENT_TIMESTAMP WHERE show_id = %s",
                    (show_id,),
                )
                cur.execute(
                    "INSERT INTO show_status_history (show_id, admin_id, previous_status, new_status, remarks) "
                    "VALUES (%s, %s, %s, 'Approved', %s)",
                    (show_id, g.user["user_id"], show["status"], "Approved from the admin portal"),
                )
        flash("Show '%s' approved." % show["title"], "success")
    except DatabaseError as exc:
        flash(str(exc), "error")
    except psycopg2.Error as exc:
        logger.error("Approve failed: %s", exc)
        flash("Approval failed due to a database error.", "error")

    return redirect(url_for("admin_shows") + "#show-%d" % show_id)


@app.route("/admin/shows/<int:show_id>/reject", methods=["POST"])
@admin_required
def admin_reject_show(show_id):
    show = get_show_or_404(show_id)
    reason = (request.form.get("reason") or "").strip()

    if len(reason) < 5:
        flash("Please provide a rejection reason (at least 5 characters).", "error")
        return redirect(url_for("admin_shows") + "#show-%d" % show_id)
    if len(reason) > 500:
        reason = reason[:500]

    try:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE shows SET status = 'Rejected', rejection_reason = %s, "
                    "updated_at = CURRENT_TIMESTAMP WHERE show_id = %s",
                    (reason, show_id),
                )
                cur.execute(
                    "INSERT INTO show_status_history (show_id, admin_id, previous_status, new_status, remarks) "
                    "VALUES (%s, %s, %s, 'Rejected', %s)",
                    (show_id, g.user["user_id"], show["status"], reason),
                )
        flash("Show '%s' rejected." % show["title"], "success")
    except DatabaseError as exc:
        flash(str(exc), "error")
    except psycopg2.Error as exc:
        logger.error("Reject failed: %s", exc)
        flash("Rejection failed due to a database error.", "error")

    return redirect(url_for("admin_shows") + "#show-%d" % show_id)


@app.route("/admin/shows/<int:show_id>/delete", methods=["POST"])
@admin_required
def admin_delete_show(show_id):
    show = get_show_or_404(show_id)
    try:
        execute("DELETE FROM shows WHERE show_id = %s", (show_id,))
        flash("Show '%s' deleted." % show["title"], "success")
    except DatabaseError as exc:
        flash(str(exc), "error")
    return redirect(url_for("admin_shows"))


@app.route("/admin/users")
@admin_required
def admin_users():
    q = (request.args.get("q") or "").strip()
    role = (request.args.get("role") or "").strip()

    clauses = ["1 = 1"]
    params = []
    if q:
        clauses.append("(u.full_name ILIKE %s OR u.email ILIKE %s OR u.agency_name ILIKE %s)")
        params.extend(["%" + q + "%", "%" + q + "%", "%" + q + "%"])
    if role in ("user", "admin"):
        clauses.append("u.role = %s")
        params.append(role)

    query = (
        "SELECT u.user_id, u.full_name, u.agency_name, u.email, u.phone, u.role, "
        "u.is_active, u.created_at, COUNT(s.show_id) AS show_count "
        "FROM users u LEFT JOIN shows s ON s.user_id = u.user_id "
        "WHERE " + " AND ".join(clauses) +
        " GROUP BY u.user_id ORDER BY u.created_at DESC"
    )

    try:
        users = fetch_all(query, params)
    except DatabaseError as exc:
        flash(str(exc), "error")
        users = []

    return render_template("admin_users.html", users=users, q=q, role=role)


@app.route("/admin/users/<int:user_id>")
@admin_required
def admin_user_detail(user_id):
    user = fetch_one("SELECT user_id, full_name, agency_name, email, phone, role, is_active, created_at "
                     "FROM users WHERE user_id = %s", (user_id,))
    if user is None:
        abort(404)
    shows = with_duration(fetch_all(
        "SELECT * FROM shows WHERE user_id = %s ORDER BY submitted_at DESC", (user_id,)
    ))
    return render_template("admin_user_detail.html", profile=user, shows=shows)


@app.route("/admin/users/<int:user_id>/toggle-status", methods=["POST"])
@admin_required
def admin_toggle_user(user_id):
    if user_id == g.user["user_id"]:
        flash("You cannot deactivate your own administrator account.", "error")
        return redirect(url_for("admin_users"))

    user = fetch_one("SELECT user_id, full_name, role, is_active FROM users WHERE user_id = %s",
                     (user_id,))
    if user is None:
        abort(404)

    new_status = not user["is_active"]
    try:
        execute("UPDATE users SET is_active = %s WHERE user_id = %s", (new_status, user_id))
        if new_status:
            flash("Account for %s activated." % user["full_name"], "success")
        else:
            flash("Account for %s deactivated. They can no longer log in." % user["full_name"], "success")
    except DatabaseError as exc:
        flash(str(exc), "error")
    return redirect(url_for("admin_users"))


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(403)
def forbidden(error):
    flash("You are not allowed to access that record.", "error")
    return redirect(url_for("index"))


@app.errorhandler(DatabaseError)
def database_problem(error):
    logger.error("Database error: %s", error)
    return render_template("error.html", message=str(error)), 503


@app.errorhandler(psycopg2.Error)
def postgres_problem(error):
    logger.error("PostgreSQL error: %s", error)
    return render_template(
        "error.html",
        message="A database error occurred. Please try again later.",
    ), 503


@app.errorhandler(500)
def server_error(error):
    logger.exception("Unhandled server error")
    return render_template(
        "error.html",
        message="Something went wrong on the server. Please try again.",
    ), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=os.getenv("FLASK_DEBUG", "1") == "1")
