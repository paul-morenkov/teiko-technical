import sqlite3
import pandas as pd

CSV_PATH = "cell-count.csv"
DB_PATH = "cell_counts.db"

SUBJECT_COLS = [
    "subject",
    "project",
    "condition",
    "age",
    "sex",
    "treatment",
    "response",
]
SAMPLE_COLS = [
    "sample",
    "subject",
    "sample_type",
    "time_from_treatment_start",
    "b_cell",
    "cd8_t_cell",
    "cd4_t_cell",
    "nk_cell",
    "monocyte",
]

CREATE_SUBJECTS = """
CREATE TABLE IF NOT EXISTS subjects (
    subject   TEXT PRIMARY KEY,
    project   TEXT,
    condition TEXT,
    age       INTEGER,
    sex       TEXT,
    treatment TEXT,
    response  TEXT
)
"""

CREATE_SAMPLES = """
CREATE TABLE IF NOT EXISTS samples (
    sample                      TEXT PRIMARY KEY,
    subject                     TEXT NOT NULL REFERENCES subjects(subject),
    sample_type                 TEXT,
    time_from_treatment_start   INTEGER,
    b_cell                      INTEGER,
    cd8_t_cell                  INTEGER,
    cd4_t_cell                  INTEGER,
    nk_cell                     INTEGER,
    monocyte                    INTEGER
)
"""

df = pd.read_csv(CSV_PATH)

con = sqlite3.connect(DB_PATH)


with con:
    cursor = con.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute(CREATE_SUBJECTS)
    cursor.execute(CREATE_SAMPLES)

subjects_df = df[SUBJECT_COLS].drop_duplicates(subset="subject")
subjects_df.to_sql("subjects", con, if_exists="replace", index=False)

samples_df = df[SAMPLE_COLS]

with con:
    samples_df.to_sql("samples", con, if_exists="replace", index=False)

n_subjects = len(subjects_df)
n_samples = len(samples_df)
print(f"Loaded {n_subjects} subjects and {n_samples} samples into {DB_PATH}")
