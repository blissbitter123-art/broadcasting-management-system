"""
generate_case_study.py
Generate the complete DBMS case study Word document.
Reads schema.sql, seed.sql, app.py, and template files from disk.
"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
import os

BASE = r"C:\Users\VICTUS\Music\DBMS\case_study"
OUTPUT_PATH = os.path.join(BASE, "Channel_Broadcasting_Management_System_DBMS_Case_Study.docx")

def read_file(relpath):
    with open(os.path.join(BASE, relpath), "r", encoding="utf-8") as f:
        return f.read()

doc = Document()

# Page setup (A4)
for section in doc.sections:
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(2.54)
    section.right_margin = Cm(2.54)

# Styles
style = doc.styles["Normal"]
style.font.name = "Times New Roman"
style.font.size = Pt(12)
style.paragraph_format.line_spacing = 1.15
style.paragraph_format.space_after = Pt(6)

for i in range(1, 5):
    hs = doc.styles["Heading %d" % i]
    hs.font.name = "Arial"
    hs.font.color.rgb = RGBColor(0, 0, 0)
    if i == 1:
        hs.font.size = Pt(16)
        hs.font.bold = True
    elif i == 2:
        hs.font.size = Pt(14)
        hs.font.bold = True
    else:
        hs.font.size = Pt(12)
        hs.font.bold = True

# Helpers
def add_centered(text, size=12, bold=False, italic=False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.name = "Times New Roman"
    return p

def add_para(text, bold=False, italic=False, size=12):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.name = "Times New Roman"
    return p

def add_code(code_text):
    for line in code_text.strip().split("\n"):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.left_indent = Cm(0.5)
        run = p.add_run(line if line else " ")
        run.font.name = "Courier New"
        run.font.size = Pt(9)
        rPr = run._element.get_or_add_rPr()
        rFonts = rPr.get_or_add_rFonts()
        rFonts.set(qn("w:ascii"), "Courier New")
        rFonts.set(qn("w:hAnsi"), "Courier New")
    doc.add_paragraph().paragraph_format.space_after = Pt(2)

def add_bullet(text):
    p = doc.add_paragraph(text, style="List Bullet")
    for run in p.runs:
        run.font.size = Pt(12)
        run.font.name = "Times New Roman"
    return p

def shade_cells(row, color="D9E2F3"):
    for cell in row.cells:
        shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color}"/>')
        cell._tc.get_or_add_tcPr().append(shading)

def add_table(headers, rows):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        run = p.add_run(str(h))
        run.font.bold = True
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    shade_cells(table.rows[0], "D9E2F3")
    for r_idx, row_data in enumerate(rows):
        for c_idx, val in enumerate(row_data):
            cell = table.rows[r_idx + 1].cells[c_idx]
            cell.text = ""
            p = cell.paragraphs[0]
            run = p.add_run(str(val))
            run.font.size = Pt(9)
            run.font.name = "Times New Roman"
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return table

def add_caption(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.font.size = Pt(10)
    run.font.bold = True
    run.font.name = "Times New Roman"

# ===========================================================================
# COVER PAGE
# ===========================================================================
for _ in range(3):
    doc.add_paragraph()

add_centered("ST. VINCENT PALLOTTI COLLEGE OF ENGINEERING & TECHNOLOGY", 16, bold=True)
add_centered("(Affiliated to University of Mumbai)", 12, italic=True)
add_centered("DEPARTMENT OF INFORMATION TECHNOLOGY", 14, bold=True)
doc.add_paragraph()
add_centered("SESSION: 2026-27", 12, bold=True)
add_centered("SEMESTER: V", 12, bold=True)
add_centered("SUBJECT: DATABASE MANAGEMENT SYSTEMS (24IT501T)", 12, bold=True)
doc.add_paragraph()
add_centered("CASE STUDY ON", 14, bold=True)
add_centered("CHANNEL BROADCASTING MANAGEMENT SYSTEM", 18, bold=True)
doc.add_paragraph()
doc.add_paragraph()

for label, value in [
    ("Submitted by:", "[Student Name]"),
    ("UID:", "[Student UID]"),
    ("Submitted to:", "[Faculty Name]"),
    ("", "Course Faculty, Department of Information Technology"),
]:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if label:
        run = p.add_run(label + " ")
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.name = "Times New Roman"
    run = p.add_run(value)
    run.font.size = Pt(12)
    run.font.name = "Times New Roman"

doc.add_page_break()

# ===========================================================================
# TABLE OF CONTENTS
# ===========================================================================
doc.add_heading("Table of Contents", level=1)
toc_items = [
    "1. Introduction",
    "2. Objectives",
    "3. Description and Problem Statement",
    "4. Table Description",
    "5. Relational Database Schema",
    "   5.1 SQL: Database and Table Creation",
    "6. E-R Diagram",
    "7. Sample Data",
    "8. SQL Operations and Expected Output",
    "   8.1 Display All Channels",
    "   8.2 Display All Registered Shows with Agency and Genre",
    "   8.3 Display the Broadcasting Schedule",
    "   8.4 Find Shows Scheduled on a Particular Date",
    "   8.5 Count Shows by Genre",
    "   8.6 Find Channels with Highest Number of Scheduled Broadcasts",
    "   8.7 Find Upcoming Scheduled Broadcasts",
    "   8.8 Find Agencies That Have Submitted Multiple Shows",
    "   8.9 Search for Shows by Title",
    "   8.10 Demonstrate a Subquery",
    "   8.11 Demonstrate Aggregate Functions",
    "   8.12 Create a Database View",
    "   8.13 INSERT Operation",
    "   8.14 UPDATE Operation",
    "   8.15 DELETE Operation",
    "   8.16 Transaction Demonstration",
    "   8.17 Schedule Conflict Detection",
    "9. Front-End Implementation and Database Connection",
    "   9.1 Tools Required",
    "   9.2 Project Folder Structure",
    "   9.3 Backend Implementation - app.py",
    "   9.4 Front-End Implementation",
    "   9.5 Connect Flask to PostgreSQL",
    "10. Testing and Validation",
    "11. Conclusion",
]
for item in toc_items:
    p = doc.add_paragraph()
    run = p.add_run(item)
    run.font.size = Pt(11)
    run.font.name = "Times New Roman"
    p.paragraph_format.space_after = Pt(2)

doc.add_page_break()

# ===========================================================================
# 1. INTRODUCTION
# ===========================================================================
doc.add_heading("1. Introduction", level=1)

doc.add_paragraph(
    "A Channel Broadcasting Management System is an information system designed to manage "
    "the complex operations of television and digital broadcasting networks. Broadcasting "
    "agencies, production houses, and channel operators must coordinate the scheduling of "
    "numerous programs across multiple channels, each with its own audience, genre, and "
    "time slot. Without a centralized system, managing show schedules, agency details, "
    "channel information, program timings, user accounts, and schedule changes becomes "
    "error-prone and inefficient."
)
doc.add_paragraph(
    "Traditional methods of maintaining broadcasting schedules rely on manual records, "
    "spreadsheets, or disconnected databases. Such approaches lead to duplicate entries, "
    "conflicting time slots, incorrect program timings, and difficulty in tracking which "
    "show airs on which channel at any given time. Unauthorized access to schedule "
    "modifications and lack of audit trails further compromise the integrity of broadcasting "
    "operations."
)
doc.add_paragraph(
    "The proposed Channel Broadcasting Management System addresses these challenges by "
    "implementing a relational database using PostgreSQL as the backend and Python Flask "
    "as the web application framework. The front-end is built using HTML, CSS, and vanilla "
    "JavaScript, rendered through Flask's Jinja2 template engine. The system provides a "
    "centralized platform where broadcasting agencies can register, submit shows with "
    "detailed metadata, and schedule broadcasts on specific channels and time slots. "
    "Administrators can oversee all operations through a secure, role-based portal."
)
doc.add_paragraph(
    "PostgreSQL was chosen for its robust support for relational integrity, advanced "
    "constraint capabilities (including exclusion constraints for schedule conflict "
    "prevention), transaction management, and ACID compliance. Flask was selected for its "
    "lightweight architecture, ease of integration with PostgreSQL via psycopg2, and "
    "suitability for academic demonstration of full-stack database application development."
)
doc.add_paragraph(
    "This case study presents a complete implementation of the system, including the "
    "relational database schema, entity-relationship design, sample data, SQL operations, "
    "Flask application code, front-end templates, and testing procedures."
)

# ===========================================================================
# 2. OBJECTIVES
# ===========================================================================
doc.add_page_break()
doc.add_heading("2. Objectives", level=1)
for obj in [
    "Design a normalized relational database for broadcasting operations covering users, agencies, channels, shows, schedules, and genres.",
    "Maintain agency, channel, show, schedule, and user records with complete referential integrity.",
    "Allow authorized users to register and log in using secure password hashing.",
    "Allow agencies or authorized users to submit shows for particular channels and time slots.",
    "Prevent invalid schedules and conflicting time slots on the same channel using PostgreSQL exclusion constraints.",
    "Use primary keys, foreign keys, UNIQUE, NOT NULL, CHECK, and DEFAULT constraints to enforce data integrity.",
    "Demonstrate INSERT, SELECT, UPDATE, DELETE, JOIN, filtering, aggregation, subqueries, views, and transactions.",
    "Connect a Flask web application to PostgreSQL using psycopg2 with parameterized queries.",
    "Provide an administrator dashboard to view and manage submitted records with role-based access control.",
    "Test database integrity and application functionality through systematic test cases.",
]:
    add_bullet(obj)

# ===========================================================================
# 3. DESCRIPTION AND PROBLEM STATEMENT
# ===========================================================================
doc.add_page_break()
doc.add_heading("3. Description and Problem Statement", level=1)

doc.add_heading("3.1 Working Scenario", level=2)
doc.add_paragraph(
    "The Channel Broadcasting Management System supports broadcasting agencies that submit "
    "television programs or shows for scheduled broadcasting. The system manages the entire "
    "lifecycle of a broadcast, from show registration by an agency to its approval by an "
    "administrator and eventual scheduling on a specific channel."
)
doc.add_paragraph(
    "A show in this system has a title, description, genre, duration, and an associated "
    "agency. A channel has its own identity and information such as channel name, type "
    "(news, entertainment, sports, etc.), and description. A schedule links a show to a "
    "channel and specifies its broadcast start time, end time, broadcast date, and status "
    "(scheduled, completed, cancelled, or live)."
)
doc.add_paragraph(
    "Registered users can log in and submit show information through web forms. An "
    "administrator can view all registered users, agencies, shows, channels, and scheduled "
    "broadcasts through a protected admin portal. The system enforces role-based access "
    "control to ensure that only authorized administrators can perform administrative "
    "operations."
)

doc.add_heading("3.2 Problem Statement", level=2)
doc.add_paragraph("The main challenges that the system solves are:")
for prob in [
    "Duplicate or incomplete show entries leading to confusion in the schedule.",
    "Incorrect broadcasting timings that cause programs to overlap or leave gaps.",
    "Overlapping schedules on the same channel, resulting in broadcast conflicts.",
    "Difficulty identifying which show will air at a particular time on a given channel.",
    "Unauthorized access to administrative operations such as schedule modification.",
    "Difficulty updating or cancelling scheduled shows in a timely manner.",
    "Lack of centralized broadcasting information across multiple agencies and channels.",
]:
    add_bullet(prob)

doc.add_heading("3.3 Assumptions and Business Rules", level=2)
for rule in [
    "Each show belongs to exactly one agency and one genre.",
    "Each show has exactly one creator (user) who submits it.",
    "One channel can have multiple scheduled broadcasts on the same day.",
    "One show can appear in multiple schedule records over time (repeat broadcasts).",
    "Each schedule entry must reference one valid show and one valid channel.",
    "A schedule's end time must be later than its start time.",
    "Overlapping schedules on the same channel for the same date are prevented at the database level.",
    "User roles are restricted to 'Admin' and 'User'.",
    "Email addresses are unique across all users and agencies.",
    "Password hashes are stored in the database; plaintext passwords are never persisted.",
    "The system uses fictional demonstration data and is not connected to real broadcasting networks.",
]:
    add_bullet(rule)

# ===========================================================================
# 4. TABLE DESCRIPTION
# ===========================================================================
doc.add_page_break()
doc.add_heading("4. Table Description", level=1)
doc.add_paragraph(
    "The database is designed with six normalized tables. Each table serves a specific "
    "purpose and maintains referential integrity through primary and foreign key constraints."
)
add_table(
    ["Table Name", "Purpose", "Key Relationship / Reason"],
    [
        ["users", "Stores user account information including administrators and regular users.", "One user can create multiple shows (one-to-many with shows)."],
        ["agencies", "Stores broadcasting agency details such as name, contact person, and address.", "One agency can register multiple shows (one-to-many with shows)."],
        ["channels", "Stores television or digital channel information.", "One channel can have multiple scheduled broadcasts (one-to-many with schedules)."],
        ["genres", "Stores genre categories for shows (e.g., News, Sports, Entertainment).", "One genre can be associated with multiple shows (one-to-many with shows)."],
        ["shows", "Stores show details including title, description, duration, and associated agency.", "Links to agencies, genres, and users via foreign keys. One show can have multiple schedules."],
        ["schedules", "Stores broadcast schedule entries linking shows to channels with date and time.", "Links to shows and channels. Prevents overlapping schedules on the same channel."],
    ],
)
add_caption("Table 4.1: Database Table Descriptions")

doc.add_heading("4.1 Relationships", level=2)
for rel in [
    "AGENCY to SHOW: One-to-Many (one agency registers multiple shows).",
    "GENRE to SHOW: One-to-Many (one genre is associated with multiple shows).",
    "USER to SHOW: One-to-Many (one user creates multiple shows).",
    "SHOW to SCHEDULE: One-to-Many (one show can have multiple schedule entries).",
    "CHANNEL to SCHEDULE: One-to-Many (one channel hosts multiple scheduled broadcasts).",
]:
    add_bullet(rel)

# ===========================================================================
# 5. RELATIONAL DATABASE SCHEMA
# ===========================================================================
doc.add_page_break()
doc.add_heading("5. Relational Database Schema", level=1)
doc.add_paragraph(
    "The database is named channel_broadcasting_management_system_portal and uses "
    "PostgreSQL's public schema. The following sections describe each table's structure, "
    "constraints, and relationships."
)

for level, title, cols in [
    (2, "5.1 Table: users", [
        ["user_id", "INTEGER", "PRIMARY KEY, IDENTITY", "Automatically generated unique user ID"],
        ["full_name", "VARCHAR(100)", "NOT NULL", "User's full name"],
        ["email", "VARCHAR(120)", "NOT NULL, UNIQUE", "User's email address"],
        ["password_hash", "VARCHAR(255)", "NOT NULL", "Hashed password (never plaintext)"],
        ["role", "VARCHAR(10)", "NOT NULL, DEFAULT 'User', CHECK", "User role: Admin or User"],
        ["created_at", "TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP", "Account creation timestamp"],
    ]),
    (2, "5.2 Table: agencies", [
        ["agency_id", "INTEGER", "PRIMARY KEY, IDENTITY", "Automatically generated unique agency ID"],
        ["agency_name", "VARCHAR(150)", "NOT NULL, UNIQUE", "Agency name"],
        ["contact_person", "VARCHAR(100)", "NOT NULL", "Primary contact person"],
        ["email", "VARCHAR(120)", "NOT NULL, UNIQUE", "Agency email address"],
        ["phone", "VARCHAR(20)", "NOT NULL", "Contact phone number"],
        ["address", "TEXT", "NOT NULL", "Agency address"],
        ["created_at", "TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP", "Record creation timestamp"],
    ]),
    (2, "5.3 Table: channels", [
        ["channel_id", "INTEGER", "PRIMARY KEY, IDENTITY", "Automatically generated unique channel ID"],
        ["channel_name", "VARCHAR(100)", "NOT NULL, UNIQUE", "Channel name"],
        ["channel_type", "VARCHAR(50)", "NOT NULL, CHECK", "Channel type: News, Entertainment, Sports, etc."],
        ["description", "TEXT", "NOT NULL", "Channel description"],
        ["active_status", "BOOLEAN", "DEFAULT TRUE", "Whether the channel is currently active"],
    ]),
    (2, "5.4 Table: genres", [
        ["genre_id", "INTEGER", "PRIMARY KEY, IDENTITY", "Automatically generated unique genre ID"],
        ["genre_name", "VARCHAR(50)", "NOT NULL, UNIQUE", "Genre name"],
        ["description", "TEXT", "NOT NULL", "Genre description"],
    ]),
    (2, "5.5 Table: shows", [
        ["show_id", "INTEGER", "PRIMARY KEY, IDENTITY", "Automatically generated unique show ID"],
        ["title", "VARCHAR(200)", "NOT NULL", "Show title"],
        ["description", "TEXT", "NOT NULL", "Show description"],
        ["agency_id", "INTEGER", "NOT NULL, FK to agencies", "Associated agency"],
        ["genre_id", "INTEGER", "NOT NULL, FK to genres", "Show genre"],
        ["duration_minutes", "INTEGER", "NOT NULL, CHECK > 0", "Show duration in minutes"],
        ["created_by", "INTEGER", "NOT NULL, FK to users", "User who created the show"],
        ["created_at", "TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP", "Record creation timestamp"],
    ]),
    (2, "5.6 Table: schedules", [
        ["schedule_id", "INTEGER", "PRIMARY KEY, IDENTITY", "Automatically generated unique schedule ID"],
        ["show_id", "INTEGER", "NOT NULL, FK to shows", "Scheduled show"],
        ["channel_id", "INTEGER", "NOT NULL, FK to channels", "Broadcast channel"],
        ["broadcast_date", "DATE", "NOT NULL", "Scheduled broadcast date"],
        ["start_time", "TIME", "NOT NULL", "Broadcast start time"],
        ["end_time", "TIME", "NOT NULL, CHECK > start_time", "Broadcast end time"],
        ["status", "VARCHAR(20)", "NOT NULL, DEFAULT 'Scheduled', CHECK", "Status: Scheduled, Completed, Cancelled, Live"],
        ["created_at", "TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP", "Record creation timestamp"],
    ]),
]:
    doc.add_heading(title, level=level)
    add_table(["Column", "Data Type", "Constraints", "Description"], cols)

doc.add_heading("5.7 Schedule Conflict Prevention", level=2)
doc.add_paragraph(
    "To prevent overlapping schedules on the same channel, PostgreSQL's btree_gist "
    "extension is used with an exclusion constraint on the schedules table. The exclusion "
    "constraint ensures that no two schedule entries for the same channel and date have "
    "overlapping time ranges."
)

# 5.1 SQL
doc.add_heading("5.1 SQL: Database and Table Creation", level=2)
doc.add_paragraph(
    "The following SQL statements create the database and all six tables. The database "
    "must be created separately, and subsequent SQL commands must be executed after "
    "connecting to it."
)
add_code(read_file("schema.sql"))

# ===========================================================================
# 6. E-R DIAGRAM
# ===========================================================================
doc.add_page_break()
doc.add_heading("6. E-R Diagram", level=1)
doc.add_paragraph(
    "The following Entity-Relationship diagram represents the database schema using "
    "Mermaid erDiagram syntax. It shows all entities, their principal attributes, "
    "primary keys, foreign keys, and cardinalities."
)
er_mermaid = """erDiagram
    USERS ||--o{ SHOWS : creates
    AGENCIES ||--o{ SHOWS : registers
    GENRES ||--o{ SHOWS : categorizes
    SHOWS ||--o{ SCHEDULES : has
    CHANNELS ||--o{ SCHEDULES : hosts

    USERS {
        integer user_id PK
        varchar full_name
        varchar email UK
        varchar password_hash
        varchar role
        timestamp created_at
    }
    AGENCIES {
        integer agency_id PK
        varchar agency_name UK
        varchar contact_person
        varchar email UK
        varchar phone
        text address
        timestamp created_at
    }
    CHANNELS {
        integer channel_id PK
        varchar channel_name UK
        varchar channel_type
        text description
        boolean active_status
    }
    GENRES {
        integer genre_id PK
        varchar genre_name UK
        text description
    }
    SHOWS {
        integer show_id PK
        varchar title
        text description
        integer agency_id FK
        integer genre_id FK
        integer duration_minutes
        integer created_by FK
        timestamp created_at
    }
    SCHEDULES {
        integer schedule_id PK
        integer show_id FK
        integer channel_id FK
        date broadcast_date
        time start_time
        time end_time
        varchar status
        timestamp created_at
    }"""
add_code(er_mermaid)
add_caption("Figure 6.1: ER Diagram (Mermaid Syntax)")

doc.add_heading("6.1 Cardinalities", level=2)
for card in [
    "USERS (1) -> (M) SHOWS: One user creates many shows.",
    "AGENCIES (1) -> (M) SHOWS: One agency registers many shows.",
    "GENRES (1) -> (M) SHOWS: One genre categorizes many shows.",
    "SHOWS (1) -> (M) SCHEDULES: One show has many schedule entries.",
    "CHANNELS (1) -> (M) SCHEDULES: One channel hosts many scheduled broadcasts.",
]:
    add_bullet(card)

# ===========================================================================
# 7. SAMPLE DATA
# ===========================================================================
doc.add_page_break()
doc.add_heading("7. Sample Data", level=1)
doc.add_paragraph(
    "The following seed data is entirely fictional and is provided for demonstration "
    "purposes only. It includes users, agencies, channels, genres, shows, and schedules "
    "with consistent foreign key references. The demo password for all accounts is "
    "Password@123 (stored as a Werkzeug scrypt hash)."
)

doc.add_heading("7.1 Row Count Summary", level=2)
add_table(
    ["Table", "Rows", "Description"],
    [
        ["users", "20", "Registered users including 2 admins and 18 regular users"],
        ["agencies", "20", "Broadcasting agencies and production houses"],
        ["channels", "20", "Television and digital channels"],
        ["genres", "20", "Show genre categories"],
        ["shows", "25", "Shows across various genres and agencies"],
        ["schedules", "25", "Scheduled broadcasts with varied statuses"],
    ],
)
add_caption("Table 7.1: Sample Data Row Counts")

doc.add_heading("7.2 Seed SQL Script", level=2)
add_code(read_file("seed.sql"))

# ===========================================================================
# 8. SQL OPERATIONS
# ===========================================================================
doc.add_page_break()
doc.add_heading("8. SQL Operations and Expected Output", level=1)
doc.add_paragraph(
    "This section demonstrates key SQL operations with complete queries and representative "
    "expected outputs. All outputs are illustrative and correspond to the sample dataset "
    "provided in Section 7."
)

# 8.1
doc.add_heading("8.1 Display All Channels", level=2)
doc.add_paragraph("Purpose: List all registered channels with their IDs, names, types, and active status.")
add_code("SELECT channel_id, channel_name, channel_type, active_status\nFROM channels\nORDER BY channel_id;")
add_caption("Expected Output (representative):")
add_table(
    ["channel_id", "channel_name", "channel_type", "active_status"],
    [
        ["1", "DD News", "News", "true"],
        ["2", "NDTV 24x7", "News", "true"],
        ["3", "Zee News", "News", "true"],
        ["4", "Aaj Tak", "News", "true"],
        ["5", "Star Sports 1", "Sports", "true"],
    ],
)
doc.add_paragraph("The query retrieves all 20 channels ordered by channel_id.")

# 8.2
doc.add_heading("8.2 Display All Registered Shows with Agency and Genre", level=2)
doc.add_paragraph("Purpose: Use INNER JOIN to display shows with their associated agency and genre names.")
add_code(
    "SELECT sh.show_id, sh.title, a.agency_name, g.genre_name, sh.duration_minutes\n"
    "FROM shows sh\n"
    "INNER JOIN agencies a ON sh.agency_id = a.agency_id\n"
    "INNER JOIN genres g   ON sh.genre_id  = g.genre_id\n"
    "ORDER BY sh.show_id;"
)
add_caption("Expected Output (representative):")
add_table(
    ["show_id", "title", "agency_name", "genre_name", "duration_minutes"],
    [
        ["1", "Morning News Roundup", "Star Media Network", "News", "60"],
        ["2", "Cricket World Cup Live", "Star Media Network", "Sports", "180"],
        ["3", "Kaun Banega Crorepati", "Sony Pictures Network", "Game Show", "60"],
        ["4", "Crime Patrol", "Viacom18 Media", "Thriller", "45"],
        ["5", "Taarak Mehta Ka Ooltah", "Colors TV", "Comedy", "30"],
    ],
)
doc.add_paragraph("INNER JOIN ensures only shows with valid agency and genre references are returned.")

# 8.3
doc.add_heading("8.3 Display the Broadcasting Schedule", level=2)
doc.add_paragraph("Purpose: Join schedules, shows, and channels to display complete broadcast information.")
add_code(
    "SELECT sh.title AS show_title, c.channel_name, s.broadcast_date,\n"
    "       s.start_time, s.end_time, s.status\n"
    "FROM schedules s\n"
    "JOIN shows sh   ON s.show_id    = sh.show_id\n"
    "JOIN channels c ON s.channel_id = c.channel_id\n"
    "ORDER BY s.broadcast_date, s.start_time;"
)
add_caption("Expected Output (representative):")
add_table(
    ["show_title", "channel_name", "broadcast_date", "start_time", "end_time", "status"],
    [
        ["Morning News Roundup", "DD News", "2026-10-20", "06:00", "07:00", "Scheduled"],
        ["Cricket World Cup Live", "Star Sports 1", "2026-10-20", "14:00", "17:00", "Scheduled"],
        ["Kaun Banega Crorepati", "Star Plus", "2026-10-20", "20:00", "21:00", "Scheduled"],
        ["Crime Patrol", "Colors TV", "2026-10-20", "22:00", "22:45", "Scheduled"],
    ],
)

# 8.4
doc.add_heading("8.4 Find Shows Scheduled on a Particular Date", level=2)
doc.add_paragraph("Purpose: Filter schedules using WHERE with a specific date.")
add_code(
    "SELECT sh.title, c.channel_name, s.start_time, s.end_time, s.status\n"
    "FROM schedules s\n"
    "JOIN shows sh   ON s.show_id    = sh.show_id\n"
    "JOIN channels c ON s.channel_id = c.channel_id\n"
    "WHERE s.broadcast_date = '2026-10-20'\n"
    "ORDER BY s.start_time;"
)
add_caption("Expected Output (representative):")
add_table(
    ["title", "channel_name", "start_time", "end_time", "status"],
    [
        ["Morning News Roundup", "DD News", "06:00", "07:00", "Scheduled"],
        ["Cricket World Cup Live", "Star Sports 1", "14:00", "17:00", "Scheduled"],
        ["Kaun Banega Crorepati", "Star Plus", "20:00", "21:00", "Scheduled"],
        ["Crime Patrol", "Colors TV", "22:00", "22:45", "Scheduled"],
    ],
)

# 8.5
doc.add_heading("8.5 Count Shows by Genre", level=2)
doc.add_paragraph("Purpose: Use GROUP BY and COUNT to show the number of shows per genre.")
add_code(
    "SELECT g.genre_name, COUNT(sh.show_id) AS show_count\n"
    "FROM genres g\n"
    "LEFT JOIN shows sh ON g.genre_id = sh.genre_id\n"
    "GROUP BY g.genre_name\n"
    "ORDER BY show_count DESC;"
)
add_caption("Expected Output (representative):")
add_table(
    ["genre_name", "show_count"],
    [
        ["Comedy", "2"],
        ["Documentary", "3"],
        ["News", "3"],
        ["Sports", "2"],
        ["Reality", "2"],
    ],
)
doc.add_paragraph("LEFT JOIN ensures genres with no shows are included with a count of 0.")

# 8.6
doc.add_heading("8.6 Find Channels with Highest Number of Scheduled Broadcasts", level=2)
doc.add_paragraph("Purpose: Use aggregation and ordering to identify the busiest channels.")
add_code(
    "SELECT c.channel_name, COUNT(s.schedule_id) AS schedule_count\n"
    "FROM channels c\n"
    "JOIN schedules s ON c.channel_id = s.channel_id\n"
    "GROUP BY c.channel_name\n"
    "ORDER BY schedule_count DESC\n"
    "LIMIT 10;"
)
add_caption("Expected Output (representative):")
add_table(
    ["channel_name", "schedule_count"],
    [
        ["Star Plus", "3"],
        ["Colors TV", "3"],
        ["Zee TV", "2"],
        ["DD News", "2"],
        ["Discovery Channel", "2"],
    ],
)

# 8.7
doc.add_heading("8.7 Find Upcoming Scheduled Broadcasts", level=2)
doc.add_paragraph(
    "Purpose: Find broadcasts scheduled for today or later. Note: The output depends on "
    "the current date at runtime. The sample data uses October 2026 dates for demonstration."
)
add_code(
    "SELECT sh.title, c.channel_name, s.broadcast_date, s.start_time, s.status\n"
    "FROM schedules s\n"
    "JOIN shows sh   ON s.show_id    = sh.show_id\n"
    "JOIN channels c ON s.channel_id = c.channel_id\n"
    "WHERE s.broadcast_date >= CURRENT_DATE\n"
    "  AND s.status IN ('Scheduled', 'Live')\n"
    "ORDER BY s.broadcast_date, s.start_time;"
)
doc.add_paragraph(
    "Note: CURRENT_DATE is evaluated at query execution time. For demonstration, "
    "replace with a fixed date such as '2026-10-20'."
)

# 8.8
doc.add_heading("8.8 Find Agencies That Have Submitted Multiple Shows", level=2)
doc.add_paragraph("Purpose: Use GROUP BY and HAVING to filter agencies with more than one show.")
add_code(
    "SELECT a.agency_name, COUNT(sh.show_id) AS show_count\n"
    "FROM agencies a\n"
    "JOIN shows sh ON a.agency_id = sh.agency_id\n"
    "GROUP BY a.agency_id, a.agency_name\n"
    "HAVING COUNT(sh.show_id) > 1\n"
    "ORDER BY show_count DESC;"
)
add_caption("Expected Output (representative):")
add_table(
    ["agency_name", "show_count"],
    [
        ["Star Media Network", "2"],
        ["Colors TV", "2"],
        ["Discovery India", "2"],
    ],
)
doc.add_paragraph("HAVING filters groups after aggregation, unlike WHERE which filters individual rows.")

# 8.9
doc.add_heading("8.9 Search for Shows by Title", level=2)
doc.add_paragraph("Purpose: Search for shows using a parameterized LIKE query.")
add_code(
    "-- Application parameterized query (Python/Flask):\n"
    "-- cursor.execute(\"SELECT * FROM shows WHERE title ILIKE %s\", ('%' + search + '%',))\n\n"
    "SELECT sh.show_id, sh.title, a.agency_name, g.genre_name\n"
    "FROM shows sh\n"
    "JOIN agencies a ON sh.agency_id = a.agency_id\n"
    "JOIN genres g   ON sh.genre_id  = g.genre_id\n"
    "WHERE sh.title ILIKE '%news%'\n"
    "ORDER BY sh.title;"
)
doc.add_paragraph("ILIKE provides case-insensitive search. Parameterized queries prevent SQL injection.")

# 8.10
doc.add_heading("8.10 Demonstrate a Subquery", level=2)
doc.add_paragraph(
    "Purpose: Identify agencies whose number of registered shows exceeds the average "
    "number of shows per agency."
)
add_code(
    "SELECT a.agency_name, COUNT(sh.show_id) AS show_count\n"
    "FROM agencies a\n"
    "JOIN shows sh ON a.agency_id = sh.agency_id\n"
    "GROUP BY a.agency_id, a.agency_name\n"
    "HAVING COUNT(sh.show_id) > (\n"
    "    SELECT AVG(show_count)\n"
    "    FROM (\n"
    "        SELECT COUNT(*) AS show_count\n"
    "        FROM shows\n"
    "        GROUP BY agency_id\n"
    "    ) AS agency_counts\n"
    ");"
)
doc.add_paragraph(
    "The subquery computes the average number of shows per agency, then the outer "
    "query filters agencies exceeding that average."
)

# 8.11
doc.add_heading("8.11 Demonstrate Aggregate Functions", level=2)
doc.add_paragraph("Purpose: Demonstrate COUNT, AVG, MIN, MAX, and SUM on meaningful columns.")
add_code(
    "SELECT\n"
    "    COUNT(*)              AS total_shows,\n"
    "    AVG(duration_minutes) AS avg_duration,\n"
    "    MIN(duration_minutes) AS min_duration,\n"
    "    MAX(duration_minutes) AS max_duration,\n"
    "    SUM(duration_minutes) AS total_duration\n"
    "FROM shows;"
)
add_caption("Expected Output (representative):")
add_table(
    ["total_shows", "avg_duration", "min_duration", "max_duration", "total_duration"],
    [["25", "61.20", "30", "180", "1530"]],
)
doc.add_paragraph("All aggregate functions operate on the numeric duration_minutes column.")

# 8.12
doc.add_heading("8.12 Create a Database View", level=2)
doc.add_paragraph("Purpose: Create a view that joins schedules, shows, and channels for easy querying.")
add_code(
    "CREATE VIEW broadcast_schedule_view AS\n"
    "SELECT\n"
    "    s.schedule_id,\n"
    "    sh.title AS show_title,\n"
    "    g.genre_name,\n"
    "    a.agency_name,\n"
    "    c.channel_name,\n"
    "    c.channel_type,\n"
    "    s.broadcast_date,\n"
    "    s.start_time,\n"
    "    s.end_time,\n"
    "    s.status,\n"
    "    sh.duration_minutes\n"
    "FROM schedules s\n"
    "JOIN shows sh   ON s.show_id    = sh.show_id\n"
    "JOIN channels c ON s.channel_id = c.channel_id\n"
    "JOIN agencies a ON sh.agency_id = a.agency_id\n"
    "JOIN genres g   ON sh.genre_id  = g.genre_id;\n\n"
    "SELECT * FROM broadcast_schedule_view\n"
    "WHERE broadcast_date = '2026-10-20'\n"
    "ORDER BY start_time;"
)
doc.add_paragraph("The view encapsulates the complex join logic for simple querying.")

# 8.13
doc.add_heading("8.13 INSERT Operation", level=2)
doc.add_paragraph("Purpose: Insert a new show with valid foreign key references.")
add_code(
    "INSERT INTO shows (title, description, agency_id, genre_id, duration_minutes, created_by)\n"
    "VALUES (\n"
    "    'Evening Prime Time News',\n"
    "    'Comprehensive evening news bulletin covering national and international headlines',\n"
    "    1,   -- agency_id: Star Media Network\n"
    "    1,   -- genre_id: News\n"
    "    45,  -- duration_minutes\n"
    "    3    -- created_by: user_id 3 (Asha Patil)\n"
    ")\n"
    "RETURNING show_id, title, created_at;"
)
doc.add_paragraph("RETURNING clause provides the newly generated show_id.")

# 8.14
doc.add_heading("8.14 UPDATE Operation", level=2)
doc.add_paragraph("Purpose: Update a show's description or change a schedule status.")
add_code(
    "-- Update a show's description\n"
    "UPDATE shows\n"
    "SET description = 'Updated: Comprehensive evening news bulletin with weather and sports'\n"
    "WHERE show_id = 1;\n\n"
    "-- Update a schedule status\n"
    "UPDATE schedules\n"
    "SET status = 'Completed'\n"
    "WHERE schedule_id = 1;\n\n"
    "-- Verify\n"
    "SELECT schedule_id, show_id, status FROM schedules WHERE schedule_id = 1;"
)
add_caption("Expected Output:")
add_table(["schedule_id", "show_id", "status"], [["1", "1", "Completed"]])

# 8.15
doc.add_heading("8.15 DELETE Operation", level=2)
doc.add_paragraph("Purpose: Delete a record only when referential integrity rules permit it.")
add_code(
    "-- Attempting to delete a show that has schedules (fails due to FK constraint)\n"
    "DELETE FROM shows WHERE show_id = 1;\n"
    "-- ERROR: update or delete on table \"shows\" violates foreign key constraint\n"
    "--        on table \"schedules\"\n\n"
    "-- First delete dependent schedules, then the show\n"
    "DELETE FROM schedules WHERE show_id = 1;\n"
    "DELETE FROM shows WHERE show_id = 1;\n\n"
    "-- Agencies referenced by shows cannot be deleted (ON DELETE RESTRICT)\n"
    "DELETE FROM agencies WHERE agency_id = 1;\n"
    "-- ERROR: update or delete on table \"agencies\" violates foreign key constraint"
)
doc.add_paragraph(
    "Foreign key constraints with ON DELETE RESTRICT prevent orphaned records. "
    "ON DELETE CASCADE on schedules.show_id automatically removes dependent schedules."
)

# 8.16
doc.add_heading("8.16 Transaction Demonstration", level=2)
doc.add_paragraph("Purpose: Demonstrate how transactions ensure consistency during multi-step operations.")
add_code(
    "BEGIN;\n\n"
    "INSERT INTO schedules (show_id, channel_id, broadcast_date, start_time, end_time, status)\n"
    "VALUES (3, 7, '2026-10-28', '20:00', '21:00', 'Scheduled');\n\n"
    "UPDATE shows\n"
    "SET description = description || ' [Scheduled on Star Plus for Oct 28]'\n"
    "WHERE show_id = 3;\n\n"
    "COMMIT;\n\n"
    "-- Verify both changes\n"
    "SELECT show_id, title FROM shows WHERE show_id = 3;\n"
    "SELECT schedule_id, show_id, broadcast_date FROM schedules WHERE show_id = 3;"
)
doc.add_paragraph(
    "BEGIN starts a transaction block. COMMIT persists all changes atomically. If any "
    "statement fails, ROLLBACK undoes all changes."
)

# 8.17
doc.add_heading("8.17 Schedule Conflict Detection", level=2)
doc.add_paragraph(
    "Purpose: Check whether a proposed schedule overlaps an existing schedule on the same channel."
)
add_code(
    "-- Application-level conflict check (before inserting)\n"
    "SELECT s.schedule_id, sh.title, s.start_time, s.end_time\n"
    "FROM schedules s\n"
    "JOIN shows sh ON s.show_id = sh.show_id\n"
    "WHERE s.channel_id = 7\n"
    "  AND s.broadcast_date = '2026-10-20'\n"
    "  AND s.status <> 'Cancelled'\n"
    "  AND s.start_time < '21:00'\n"
    "  AND s.end_time   > '20:00';\n\n"
    "-- Database-level protection: exclusion constraint\n"
    "-- The following INSERT will fail if it overlaps an existing schedule\n"
    "INSERT INTO schedules (show_id, channel_id, broadcast_date, start_time, end_time, status)\n"
    "VALUES (4, 7, '2026-10-20', '20:30', '21:30', 'Scheduled');\n"
    "-- ERROR: conflicting key value violates exclusion constraint \"no_overlap\""
)
doc.add_paragraph(
    "The exclusion constraint provides database-level protection against overlapping "
    "schedules, even under concurrent access."
)

# ===========================================================================
# 9. FRONT-END IMPLEMENTATION
# ===========================================================================
doc.add_page_break()
doc.add_heading("9. Front-End Implementation and Database Connection", level=1)

doc.add_heading("9.1 Tools Required", level=2)
add_table(
    ["Tool", "Purpose"],
    [
        ["PostgreSQL", "Relational database management system for storing all data."],
        ["pgAdmin 4", "Graphical administration tool for managing PostgreSQL databases."],
        ["Python 3.10+", "Programming language for the Flask backend."],
        ["Flask", "Lightweight web framework for routing and templating."],
        ["psycopg2-binary", "PostgreSQL adapter for Python."],
        ["Modern Web Browser", "For accessing the web application interface."],
    ],
)

doc.add_heading("9.2 Project Folder Structure", level=2)
add_code(
    "channel_broadcasting_management_system_portal/\n"
    "├── app.py                  # Flask application with all routes\n"
    "├── schema.sql              # Database schema creation script\n"
    "├── seed.sql                # Sample data insertion script\n"
    "├── requirements.txt        # Python dependencies\n"
    "├── .env                    # Environment variables (not committed)\n"
    "├── templates/\n"
    "│   ├── base.html           # Base template with navigation\n"
    "│   ├── index.html          # Home page with dashboard statistics\n"
    "│   ├── login.html          # User login page\n"
    "│   ├── register.html       # User registration page\n"
    "│   ├── shows.html          # Show listing page\n"
    "│   ├── add_show.html       # Show submission form\n"
    "│   ├── schedule.html       # Broadcasting schedule page\n"
    "│   └── admin.html          # Administrator dashboard\n"
    "└── static/\n"
    "    ├── style.css           # CSS styles\n"
    "    └── script.js           # JavaScript for client-side interactions"
)

doc.add_heading("9.3 Backend Implementation - app.py", level=2)
doc.add_paragraph("The following is the complete Flask application code:")
add_code(read_file("app.py"))

doc.add_heading("9.4 Front-End Implementation", level=2)
doc.add_paragraph(
    "The front-end uses HTML5, CSS3, and vanilla JavaScript with Flask's Jinja2 "
    "template engine."
)

doc.add_heading("9.4.1 Base Template (base.html)", level=3)
add_code(read_file("templates/base.html"))

doc.add_heading("9.4.2 Index Template (index.html)", level=3)
add_code(read_file("templates/index.html"))

doc.add_heading("9.4.3 CSS Styles (style.css)", level=3)
add_code(read_file("static/style.css"))

doc.add_heading("9.5 Connect Flask to PostgreSQL", level=2)
doc.add_paragraph("Follow these steps to set up and run the application:")
for step in [
    "1. Create the database: Execute CREATE DATABASE channel_broadcasting_management_system_portal; in psql or pgAdmin.",
    "2. Execute schema.sql: Run the schema script to create all tables and constraints.",
    "3. Execute seed.sql: Run the seed script to populate sample data.",
    "4. Install Python packages: Run pip install -r requirements.txt.",
    "5. Configure environment variables: Create a .env file with DB credentials and SECRET_KEY.",
    "6. Create administrator: Insert an admin user with a hashed password using Werkzeug.",
    "7. Run the application: Execute python app.py.",
    "8. Open browser: Navigate to http://127.0.0.1:5000.",
    "9. Log in as normal user: Register a new account and log in.",
    "10. Submit a show: Fill the add-show form and verify it appears in PostgreSQL.",
    "11. Log in as administrator: Access the admin portal and verify all records are visible.",
]:
    add_bullet(step)

add_code(
    "# Example .env file\n"
    "DB_HOST=localhost\n"
    "DB_PORT=5432\n"
    "DB_NAME=channel_broadcasting_management_system_portal\n"
    "DB_USER=postgres\n"
    "DB_PASSWORD=your_password_here\n"
    "SECRET_KEY=your-secret-key-here\n\n"
    "# Install dependencies\n"
    "pip install Flask psycopg2-binary python-dotenv Werkzeug\n\n"
    "# Run the application\n"
    "python app.py"
)

# ===========================================================================
# 10. TESTING
# ===========================================================================
doc.add_page_break()
doc.add_heading("10. Testing and Validation", level=1)
doc.add_paragraph(
    "The following test cases validate the system's functionality. Expected results "
    "are documented based on the system design and business rules."
)
add_table(
    ["Test Case", "Action", "Expected Result"],
    [
        ["TC-01: Valid user registration", "Fill all fields with valid data and submit.", "Account created, user redirected to login page."],
        ["TC-02: Duplicate email registration", "Register with an existing email address.", "Error message: Email already registered."],
        ["TC-03: Valid login", "Enter correct email and password.", "User logged in, redirected to dashboard."],
        ["TC-04: Invalid login", "Enter incorrect password.", "Error: Invalid email or password."],
        ["TC-05: Unauthorized admin access", "Access /admin without admin role.", "Redirected to home page with error message."],
        ["TC-06: Authorized admin login", "Login with admin credentials.", "Admin dashboard displayed with all records."],
        ["TC-07: Add show with valid data", "Submit show form with all valid fields.", "Show saved, appears in show listing."],
        ["TC-08: Add show with invalid agency ID", "Submit form with non-existent agency_id.", "Foreign key constraint violation error."],
        ["TC-09: Create schedule for invalid channel", "Use non-existent channel_id.", "Foreign key constraint violation."],
        ["TC-10: Schedule with end before start", "Set end_time earlier than start_time.", "CHECK constraint violation or validation error."],
        ["TC-11: Overlapping schedule on same channel", "Create schedule overlapping existing one.", "Exclusion constraint violation: conflict detected."],
        ["TC-12: Non-conflicting schedule", "Create schedule with no overlap.", "Schedule created successfully."],
        ["TC-13: Update schedule status", "Change status from Scheduled to Completed.", "Status updated in database."],
        ["TC-14: Cancel scheduled broadcast", "Set status to Cancelled.", "Status updated, schedule excluded from conflict checks."],
        ["TC-15: Search for a show", "Enter search term in show search.", "Matching shows displayed in results."],
        ["TC-16: View joined schedule info", "Access schedule page.", "Shows with agency, genre, channel displayed correctly."],
        ["TC-17: Dashboard statistics", "View home page.", "Correct counts displayed for shows, users, channels, schedules."],
        ["TC-18: Foreign-key integrity", "Delete agency with associated shows.", "ON DELETE RESTRICT prevents deletion."],
        ["TC-19: Database connectivity", "Start application with PostgreSQL running.", "Application starts without connection errors."],
        ["TC-20: Password hash verification", "Check users table after registration.", "password_hash contains hashed value, not plaintext."],
    ],
)
add_caption("Table 10.1: Test Cases and Expected Results")
doc.add_paragraph(
    "Note: Expected results are based on the system design. Actual test execution should "
    "be performed by running the application with the PostgreSQL database."
)

# ===========================================================================
# 11. CONCLUSION
# ===========================================================================
doc.add_page_break()
doc.add_heading("11. Conclusion", level=1)
doc.add_paragraph(
    "The Channel Broadcasting Management System demonstrates the practical application "
    "of relational database design principles in a real-world broadcasting scenario. "
    "The system successfully implements a normalized database schema with six related "
    "tables, ensuring data integrity through primary keys, foreign keys, UNIQUE, NOT NULL, "
    "CHECK, and DEFAULT constraints."
)
doc.add_paragraph("Key DBMS concepts demonstrated in this project include:")
for item in [
    "Normalization: The database is designed in third normal form (3NF), eliminating data redundancy.",
    "Referential Integrity: Foreign key constraints with ON DELETE RESTRICT and CASCADE ensure consistency.",
    "Constraint Enforcement: CHECK constraints validate data values; UNIQUE constraints prevent duplicates.",
    "Exclusion Constraints: The btree_gist extension prevents overlapping schedules on the same channel.",
    "SQL Operations: The system demonstrates INSERT, SELECT, UPDATE, DELETE, JOIN, GROUP BY, HAVING, subqueries, views, and transactions.",
    "Application Integration: Flask connects to PostgreSQL using parameterized queries, preventing SQL injection.",
    "Role-Based Access Control: The system distinguishes between regular users and administrators.",
]:
    add_bullet(item)
doc.add_paragraph(
    "The centralized scheduling system eliminates problems associated with manual "
    "broadcast management, including duplicate entries, conflicting time slots, and "
    "difficulty tracking which show airs on which channel."
)
doc.add_heading("11.1 Future Enhancements", level=2)
for item in [
    "Automated Notifications: Send email or SMS alerts when shows are approved or schedules change.",
    "Recurring Broadcasts: Support shows that air on a recurring basis (daily, weekly, monthly).",
    "Analytics Dashboard: Add reporting features with charts showing viewership trends and prime-time utilization.",
    "Audit Logs: Maintain detailed logs of all database changes for compliance and debugging.",
    "Schedule Conflict Alerts: Provide real-time visual warnings for overlapping schedules.",
    "Integration with External Systems: Connect with electronic program guide (EPG) systems.",
]:
    add_bullet(item)
doc.add_paragraph(
    "This project provides a solid foundation for understanding how relational databases "
    "can be applied to complex real-world problems. The skills demonstrated here are "
    "essential for any aspiring database administrator or full-stack developer."
)

# ===========================================================================
# SAVE
# ===========================================================================
doc.save(OUTPUT_PATH)
print("Document saved successfully:", OUTPUT_PATH)
print("File size:", os.path.getsize(OUTPUT_PATH), "bytes")
