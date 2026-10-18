# Channel Broadcasting Management System - DBMS Case Study

A complete, submission-ready DBMS case study project for **Channel Broadcasting Management System**.

## Contents

This folder contains all deliverables for the DBMS case study:

1. **Channel_Broadcasting_Management_System_DBMS_Case_Study.docx** - Complete Word document
2. **schema.sql** - Database schema creation script
3. **seed.sql** - Sample data insertion script
4. **app.py** - Flask application
5. **templates/** - HTML templates (Jinja2)
6. **static/** - CSS and JavaScript files
7. **requirements.txt** - Python dependencies
8. **.env.example** - Environment variable template

## Setup Instructions

### 1. Create the database

```sql
CREATE DATABASE channel_broadcasting_management_system_portal;
```

### 2. Execute schema.sql

```bash
psql -U postgres -d channel_broadcasting_management_system_portal -f schema.sql
```

### 3. Execute seed.sql

```bash
psql -U postgres -d channel_broadcasting_management_system_portal -f seed.sql
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment

Copy `.env.example` to `.env` and update the values:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=channel_broadcasting_management_system_portal
DB_USER=postgres
DB_PASSWORD=your_password
SECRET_KEY=your-secret-key
```

### 6. Run the application

```bash
python app.py
```

Open http://127.0.0.1:5000 in your browser.

## Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@cbms.local | Password@123 |
| User | asha@example.com | Password@123 |

## Project Structure

```
case_study/
├── app.py                  # Flask application
├── schema.sql              # Database schema
├── seed.sql                # Sample data
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template
├── README.md               # This file
├── templates/
│   ├── base.html           # Base template
│   ├── index.html          # Home page
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   ├── shows.html          # Show listing
│   ├── add_show.html       # Show submission form
│   ├── schedule.html       # Broadcasting schedule
│   └── admin.html          # Admin dashboard
└── static/
    ├── style.css           # CSS styles
    └── script.js           # JavaScript
```
