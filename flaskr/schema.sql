-- Initialize the database.
-- Drop any existing data and create empty tables.

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS subject;
DROP TABLE IF EXISTS assignment;
DROP TABLE IF EXISTS timetable;
DROP TABLE IF EXISTS timetable_select;


--  User Information
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    password TEXT NOT NULL
);

CREATE TABLE post (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author_id INTEGER NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    FOREIGN KEY (author_id) REFERENCES user (id)
);

-- Subject DB (database)
CREATE TABLE subject (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_name TEXT NOT NULL,
    teacher_name TEXT,
    classroom INTEGER
);

-- Assignment DB
CREATE TABLE assignment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_name TEXT NOT NULL,
    contents TEXT,
    deadline TEXT NOT NULL,
    classroom INTEGER,
    FOREIGN KEY (subject_name) REFERENCES subject (subject_name),
    FOREIGN KEY (classroom) REFERENCES subject (classroom)
);

CREATE TABLE timetable(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_id INTEGER NOT NULL,
    time TEXT  NOT NULL,
    subject_name TEXT NOT NULL,
    FOREIGN KEY (subject_name) REFERENCES subject (subject_name)
);


CREATE TABLE timetable_select(
    table_id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    vertical INTEGER NOT NULL,
    horizontal INTEGER NOT NULL,
    FOREIGN KEY (table_id) REFERENCES timetable (table_id) 
)