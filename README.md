# BroadcastHub - Channel Broadcasting Management System

A complete, beginner-friendly **Channel Broadcasting Management System** built with
**Flask + PostgreSQL + HTML + CSS + vanilla JavaScript** for a college DBMS project.

Broadcasting agencies, production houses and individual users can register, list their
shows with full broadcast schedules, and track approval status. A separate, secure
administrator portal lets an admin monitor every user, every show, approve or reject
submissions, and manage accounts - all backed by a real PostgreSQL database.

---

## 1. Project structure

```
C:\Users\VICTUS\Music\DBMS\
│
├── app.py                 # All Flask routes (public, user, admin)
├── database.py            # Database helpers, table creation, admin creation
├── requirements.txt       # Python dependencies
├── .env                   # Local secrets (database password, secret key) - never commit
├── .env.example           # Placeholder copy of .env
├── .gitignore
│
├── templates/
│   ├── base.html              # Shared navigation + footer
│   ├── index.html             # Homepage
│   ├── login.html             # User login
│   ├── register.html          # User registration
│   ├── dashboard.html         # User dashboard
│   ├── add_show.html          # List a new show
│   ├── edit_show.html         # Edit an existing show
│   ├── show_details.html      # Single show details (user + admin views)
│   ├── my_shows.html          # User's own show list
│   ├── shows.html             # Public approved schedule (browse/search/filter)
│   ├── admin_login.html       # Administrator login
│   ├── admin_dashboard.html   # Admin overview + recent submissions
│   ├── admin_shows.html       # Admin show management
│   ├── admin_users.html       # Admin user management
│   ├── admin_user_detail.html # One user's profile + their shows
│   ├── 404.html               # Custom not-found page
│   └── error.html             # Friendly database / server error page
│
├── static/
│   ├── css/style.css          # All styling (responsive)
│   ├── js/script.js           # Mobile nav, duration calc, confirmations
│   └── images/
│
└── README.md
```

---

## 2. What you need installed (one time)

### Step 1 - Install Python

1. Download Python 3.11 or newer from https://www.python.org/downloads/
2. Run the installer and **tick "Add python.exe to PATH"** on the first screen.
3. Click *Install Now*.
4. Verify by opening **Command Prompt** and typing:

```bat
python --version
```

You should see something like `Python 3.14.6`.

### Step 2 - Install PostgreSQL

1. Download PostgreSQL from https://www.postgresql.org/download/windows/
2. Run the installer (the EDB installer is easiest).
3. Remember the **password you set for the `postgres` user** - you will need it in `.env`.
4. Keep the default port **5432**.
5. Finish the installation and make sure the service is running
   (Services app → *postgresql-x64-18* → should say *Running*).

---

## 3. Open the project in VS Code

1. Install VS Code from https://code.visualstudio.com/
2. Open **File → Open Folder** and choose `C:\Users\VICTUS\Music\DBMS`.
3. Open a terminal inside VS Code with **Ctrl + `** (backtick).

---

## 4. Create and activate a virtual environment

In the VS Code terminal (or Command Prompt), run these commands **inside the project folder**:

```bat
cd C:\Users\VICTUS\Music\DBMS
python -m venv venv
```

Activate it:

**Command Prompt:**

```bat
venv\Scripts\activate.bat
```

**PowerShell:**

```powershell
venv\Scripts\Activate.ps1
```

Your prompt should now start with `(venv)`.

---

## 5. Install the Python dependencies

With the virtual environment activated:

```bat
pip install -r requirements.txt
```

Dependencies: `Flask`, `Flask-WTF` (CSRF protection), `psycopg2-binary` (PostgreSQL driver),
`python-dotenv` (reads `.env`), `Werkzeug` (password hashing), and `gunicorn` (Render web server).

---

## 6. Configure the `.env` file

The project already contains a `.env` file. Open it and make sure it matches your machine:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=broadcasting_management
DB_USER=postgres
DB_PASSWORD=your_postgresql_password
SECRET_KEY=replace_with_a_random_secret_key
FLASK_DEBUG=1
SESSION_COOKIE_SECURE=false
```

* `DB_USER` / `DB_PASSWORD` = your own PostgreSQL username and password.
* `SECRET_KEY` = any long random text (used for secure sessions and CSRF tokens).
* **Never commit `.env` to git** - it is listed in `.gitignore`.

---

## Hosting on Render

The repository includes a [`render.yaml`](./render.yaml) Blueprint that provisions a
Python web service and PostgreSQL database. The web service runs the idempotent schema
setup command before starting Gunicorn. Render supplies `DATABASE_URL` and generates
a `SECRET_KEY`; HTTPS-only session cookies are enabled for the hosted site.

1. Push this project to a GitHub repository. Do not commit `.env`, credentials, or
   other secrets.
2. In Render, choose **New → Blueprint**, connect the GitHub repository, and deploy
   the detected `render.yaml`.
3. Wait for both the web service and database to finish provisioning. Open the web
   service's `onrender.com` URL.
4. Create the first administrator from the web service's **Shell** using:

   ```sh
   python database.py admin
   ```

   Enter the administrator details at the prompts. Then sign in at
   `/admin/login`.

The schema setup is safe to run on each service start because its table and index
definitions use `IF NOT EXISTS`. For local development, continue using `.env` and
`python database.py init`; `python database.py schema` only creates tables in the
currently configured database.

> Render's free PostgreSQL plan may have availability or lifetime limits. Check the
> current plan details in Render before relying on it for persistent production data.

---

## 7. Create the database and tables

The database name for this project is **`broadcasting_management`**.

Run the included initialisation command (with the virtual environment active):

```bat
python database.py init
```

This will:

1. Connect to PostgreSQL.
2. Create the database `broadcasting_management` if it does not exist.
3. Create the tables `users`, `shows` and `show_status_history`
   with primary keys, foreign keys, `CHECK`, `UNIQUE`, `DEFAULT` constraints and indexes.

You do **not** need to create tables by hand in pgAdmin or psql.

---

## 8. Create the first administrator account

Administrators can never self-register on the website. Create the first admin securely
from the terminal (the password is hidden while typing):

```bat
python database.py admin
```

Enter the full name, agency, email, phone and a strong password when prompted.

---

## 9. Run the application

```bat
python app.py
```

Then open your browser at:

**http://127.0.0.1:5000**

Stop the server with `Ctrl + C` in the terminal.

---

## 10. How to log in

### Normal user

1. Open http://127.0.0.1:5000/register and create an account.
2. Open http://127.0.0.1:5000/login and sign in.
3. Use *List a New Show* to submit a show (status starts as **Pending**).

### Administrator

1. Open http://127.0.0.1:5000/admin/login (or the *Admin Portal* link in the footer).
2. Sign in with the admin account you created in step 8.
3. Approve or reject shows, and activate/deactivate users.

### Demo accounts (already seeded for the demonstration)

| Role          | Email                    | Password  |
|---------------|--------------------------|-----------|
| Administrator | admin@broadcasthub.local | Admin@123 |
| User (demo)   | asha@example.com         | secret123 |

> For a submission you can mark these in your report, create your own accounts with
> `python database.py admin` / the Register page instead.

---

## 11. Database design (relationships)

**`users`** (1) ----< (`shows`) (many) ----< (`show_status_history`) (many)

* A **user** (agency) submits many **shows** (`shows.user_id` → `users.user_id`, `ON DELETE RESTRICT`).
  You cannot delete a user while their shows still exist, so there are never orphaned shows.
* Each **show** can have many **status history** rows (`show_status_history.show_id` →
  `shows.show_id`, `ON DELETE CASCADE`). Deleting a show removes only its history.
* `show_status_history.admin_id` → `users.user_id` records **which administrator**
  approved or rejected the show (`ON DELETE SET NULL`).

Verify the data really reached PostgreSQL:

```bat
psql -U postgres -d broadcasting_management -c "SELECT * FROM users;"
psql -U postgres -d broadcasting_management -c "SELECT show_id, title, status FROM shows;"
psql -U postgres -d broadcasting_management -c "SELECT * FROM show_status_history;"
```

Or open **pgAdmin** → Databases → `broadcasting_management` → Tables → *View/Edit Data*.

---

## 12. Troubleshooting common PostgreSQL errors

| Problem | Fix |
|---|---|
| `Could not connect to PostgreSQL` | Open Windows *Services* and start `postgresql-x64-18`. |
| `password authentication failed` | Fix `DB_USER` / `DB_PASSWORD` in `.env` to match your PostgreSQL install. |
| `database "broadcasting_management" does not exist` | Run `python database.py init`. |
| `psql` is not recognized | Add `C:\Program Files\PostgreSQL\18\bin` to your system PATH, or use pgAdmin. |
| `ModuleNotFoundError: No module named 'flask'` | Activate the virtual environment (`venv\Scripts\activate.bat`) and re-run `pip install -r requirements.txt`. |
| Port 5000 already in use | Close the other program, or edit the `app.run(...)` port in `app.py`. |
| Changes to `.env` not picked up | Stop the server with Ctrl+C and run `python app.py` again. |

If the site shows *"Something went wrong"*, PostgreSQL is probably not running or the
`.env` credentials are wrong. Check the terminal window for the detailed log message.

---

## 13. Security features included

* Passwords hashed with Werkzeug (`generate_password_hash`) - plaintext is never stored.
* All SQL uses **parameterised queries** (`%s` placeholders) - no string concatenation.
* CSRF protection on every POST form (Flask-WTF).
* Server-side validation of every field, date, time and schedule.
* Ownership checks - users can only view/edit/delete **their own** shows.
* Role checks (`login_required`, `admin_required` decorators) on the server, not hidden links.
* Deactivated users cannot log in or use protected pages.
* Admins cannot deactivate their own account.
* Session cookies: `HttpOnly`, `SameSite=Lax`; set `SESSION_COOKIE_SECURE=true` when
  serving over HTTPS (the Render Blueprint does this).
* Schedule overlap checks against existing **approved** shows block conflicting approvals.

---

## 14. Feature checklist (what to demo)

1. Homepage shows live approved shows from PostgreSQL.
2. Register → duplicate email is rejected.
3. Login / logout with secure sessions.
4. Submit a show → saved as **Pending**, appears in *My Shows*.
5. Invalid schedule (end before start, past date) is rejected.
6. Another user cannot edit or delete your show.
7. Pending/rejected shows are **not** visible on the public schedule.
8. Admin logs in at `/admin/login`; normal users are blocked from `/admin/*`.
9. Admin approves a show → it instantly appears on the public schedule.
10. Approval/rejection is recorded in `show_status_history`.
11. Admin rejects with a reason → the owner sees the reason.
12. Overlapping shows on the same channel are flagged and cannot be approved.
13. Admin searches/filters shows by title, agency, status, channel and date.
14. Admin deactivates a user → that user cannot log in.
15. Website is responsive on desktop, tablet and mobile.

---

## 15. Resetting the project (start fresh)

```bat
psql -U postgres -c "DROP DATABASE broadcasting_management;"
python database.py init
python database.py admin
```

Then register a normal user from the website and start listing shows.

---

## 16. Technology summary

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, Vanilla JavaScript, Jinja2 templates |
| Backend | Python, Flask |
| Database | PostgreSQL with `psycopg2-binary` |
| Authentication | Flask sessions, Werkzeug password hashing, role-based access |
| Security | Flask-WTF CSRF, parameterised SQL, server-side validation |

No React, Angular, Vue, Node.js, PHP, MongoDB, Docker or microservices - just a clean,
compact, easy-to-explain Flask + PostgreSQL project.
