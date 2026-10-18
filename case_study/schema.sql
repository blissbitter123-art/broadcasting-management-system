-- =====================================================
-- Channel Broadcasting Management System
-- Database: channel_broadcasting_management_system_portal
-- =====================================================

-- Step 1: Create the database (run separately in psql/pgAdmin)
-- CREATE DATABASE channel_broadcasting_management_system_portal;

-- Step 2: Connect to the database before running the commands below
-- In psql:  \c channel_broadcasting_management_system_portal

-- Step 3: Enable btree_gist for exclusion constraints
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- =====================================================
-- TABLE 1: users
-- =====================================================
CREATE TABLE users (
    user_id       INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name     VARCHAR(100) NOT NULL,
    email         VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(10)  NOT NULL DEFAULT 'User'
                  CHECK (role IN ('Admin', 'User')),
    created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLE 2: agencies
-- =====================================================
CREATE TABLE agencies (
    agency_id      INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    agency_name    VARCHAR(150) NOT NULL UNIQUE,
    contact_person VARCHAR(100) NOT NULL,
    email          VARCHAR(120) NOT NULL UNIQUE,
    phone          VARCHAR(20)  NOT NULL,
    address        TEXT         NOT NULL,
    created_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLE 3: channels
-- =====================================================
CREATE TABLE channels (
    channel_id    INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_name  VARCHAR(100) NOT NULL UNIQUE,
    channel_type  VARCHAR(50)  NOT NULL
                  CHECK (channel_type IN ('News','Entertainment','Sports',
                        'Educational','Music','Documentary','Regional','Digital')),
    description   TEXT         NOT NULL,
    active_status BOOLEAN      NOT NULL DEFAULT TRUE
);

-- =====================================================
-- TABLE 4: genres
-- =====================================================
CREATE TABLE genres (
    genre_id    INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    genre_name  VARCHAR(50) NOT NULL UNIQUE,
    description TEXT        NOT NULL
);

-- =====================================================
-- TABLE 5: shows
-- =====================================================
CREATE TABLE shows (
    show_id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title            VARCHAR(200) NOT NULL,
    description      TEXT         NOT NULL,
    agency_id        INTEGER      NOT NULL REFERENCES agencies(agency_id)
                       ON DELETE RESTRICT,
    genre_id         INTEGER      NOT NULL REFERENCES genres(genre_id)
                       ON DELETE RESTRICT,
    duration_minutes INTEGER      NOT NULL CHECK (duration_minutes > 0),
    created_by       INTEGER      NOT NULL REFERENCES users(user_id)
                       ON DELETE RESTRICT,
    created_at       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLE 6: schedules
-- =====================================================
CREATE TABLE schedules (
    schedule_id    INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    show_id        INTEGER NOT NULL REFERENCES shows(show_id)
                       ON DELETE CASCADE,
    channel_id     INTEGER NOT NULL REFERENCES channels(channel_id)
                       ON DELETE RESTRICT,
    broadcast_date DATE    NOT NULL,
    start_time     TIME    NOT NULL,
    end_time       TIME    NOT NULL,
    status         VARCHAR(20) NOT NULL DEFAULT 'Scheduled'
                   CHECK (status IN ('Scheduled','Completed','Cancelled','Live')),
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_time_order CHECK (end_time > start_time),
    CONSTRAINT no_overlap
        EXCLUDE USING gist (
            channel_id WITH =,
            daterange(broadcast_date, broadcast_date, '[]') WITH &&
        )
        WHERE (status <> 'Cancelled')
);

-- =====================================================
-- INDEXES
-- =====================================================
CREATE INDEX idx_shows_agency       ON shows(agency_id);
CREATE INDEX idx_shows_genre        ON shows(genre_id);
CREATE INDEX idx_shows_creator      ON shows(created_by);
CREATE INDEX idx_schedules_show     ON schedules(show_id);
CREATE INDEX idx_schedules_channel  ON schedules(channel_id);
CREATE INDEX idx_schedules_date     ON schedules(broadcast_date);
CREATE INDEX idx_users_email        ON users(email);

-- =====================================================
-- VIEW: broadcast_schedule_view
-- =====================================================
CREATE VIEW broadcast_schedule_view AS
SELECT
    s.schedule_id,
    sh.title AS show_title,
    g.genre_name,
    a.agency_name,
    c.channel_name,
    c.channel_type,
    s.broadcast_date,
    s.start_time,
    s.end_time,
    s.status,
    sh.duration_minutes
FROM schedules s
JOIN shows sh     ON s.show_id    = sh.show_id
JOIN channels c   ON s.channel_id = c.channel_id
JOIN agencies a   ON sh.agency_id = a.agency_id
JOIN genres g     ON sh.genre_id  = g.genre_id;
