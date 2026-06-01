import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "nutricoach.db")


def _connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                email         TEXT UNIQUE,
                name          TEXT,
                age           INTEGER,
                sex           TEXT,
                height_cm     REAL,
                weight_kg     REAL,
                activity_level TEXT,
                fitness_goal  TEXT,
                health_conditions TEXT,
                diet_pref     TEXT,
                cuisine_prefs TEXT,
                bmr           INTEGER,
                tdee          INTEGER,
                base_calories INTEGER,
                created_at    TEXT,
                updated_at    TEXT
            )
        """)
        conn.commit()


def save_profile(profile: dict):
    init_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    email = profile.get("email", "").strip() or None

    with _connect() as conn:
        if email:
            # Upsert on email
            existing = conn.execute("SELECT id FROM profiles WHERE email = ?", (email,)).fetchone()
            if existing:
                conn.execute("""
                    UPDATE profiles SET
                        name=?, age=?, sex=?, height_cm=?, weight_kg=?,
                        activity_level=?, fitness_goal=?, health_conditions=?,
                        diet_pref=?, cuisine_prefs=?, bmr=?, tdee=?,
                        base_calories=?, updated_at=?
                    WHERE email=?
                """, (
                    profile["name"], profile["age"], profile["sex"],
                    profile["height_cm"], profile["weight_kg"],
                    profile["activity_level"], profile["fitness_goal"],
                    ",".join(profile.get("health_conditions", [])),
                    profile["diet_pref"],
                    ",".join(profile.get("cuisine_prefs", [])),
                    profile["bmr"], profile["tdee"], profile["base_calories"],
                    now, email,
                ))
            else:
                conn.execute("""
                    INSERT INTO profiles
                        (email, name, age, sex, height_cm, weight_kg, activity_level,
                         fitness_goal, health_conditions, diet_pref, cuisine_prefs,
                         bmr, tdee, base_calories, created_at, updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    email, profile["name"], profile["age"], profile["sex"],
                    profile["height_cm"], profile["weight_kg"],
                    profile["activity_level"], profile["fitness_goal"],
                    ",".join(profile.get("health_conditions", [])),
                    profile["diet_pref"],
                    ",".join(profile.get("cuisine_prefs", [])),
                    profile["bmr"], profile["tdee"], profile["base_calories"],
                    now, now,
                ))
        else:
            conn.execute("""
                INSERT INTO profiles
                    (name, age, sex, height_cm, weight_kg, activity_level,
                     fitness_goal, health_conditions, diet_pref, cuisine_prefs,
                     bmr, tdee, base_calories, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                profile["name"], profile["age"], profile["sex"],
                profile["height_cm"], profile["weight_kg"],
                profile["activity_level"], profile["fitness_goal"],
                ",".join(profile.get("health_conditions", [])),
                profile["diet_pref"],
                ",".join(profile.get("cuisine_prefs", [])),
                profile["bmr"], profile["tdee"], profile["base_calories"],
                now, now,
            ))
        conn.commit()


def load_profile_by_email(email: str) -> dict | None:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM profiles WHERE email = ?", (email,)
        ).fetchone()
    return _row_to_dict(conn, row) if row else None


def load_latest_profile() -> dict | None:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM profiles ORDER BY updated_at DESC LIMIT 1"
        ).fetchone()
        if not row:
            return None
        cols = [d[0] for d in conn.execute("SELECT * FROM profiles LIMIT 0").description]
    return _row_to_dict_cols(row, cols)


def get_all_profiles() -> list[dict]:
    init_db()
    with _connect() as conn:
        cursor = conn.execute("SELECT * FROM profiles ORDER BY updated_at DESC")
        cols = [d[0] for d in cursor.description]
        return [_row_to_dict_cols(row, cols) for row in cursor.fetchall()]


def delete_profile(profile_id: int):
    init_db()
    with _connect() as conn:
        conn.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
        conn.commit()


def _row_to_dict_cols(row, cols):
    d = dict(zip(cols, row))
    d["health_conditions"] = d["health_conditions"].split(",") if d.get("health_conditions") else []
    d["cuisine_prefs"]     = d["cuisine_prefs"].split(",")     if d.get("cuisine_prefs")     else []
    return d


def _row_to_dict(conn, row):
    cols = [d[0] for d in conn.execute("SELECT * FROM profiles LIMIT 0").description]
    return _row_to_dict_cols(row, cols)
