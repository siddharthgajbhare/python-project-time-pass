"""
Attendance Management API (extended)
"""
import csv
import io
import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import Flask, request, jsonify, g, Response

app = Flask(__name__)
DATABASE = os.environ.get("ATTENDANCE_DB", "attendance.db")
API_KEY = os.environ.get("ATTENDANCE_API_KEY")  # if unset, auth is disabled
VALID_STATUSES = {"present", "late", "absent", "excused"}


# --------------------------------------------------------------------------
# Database helpers
# --------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT
        );
        CREATE TABLE IF NOT EXISTS classes (
            id TEXT PRIMARY KEY,
            name TEXT,
            teacher TEXT,
            late_after TEXT              -- 'HH:MM'; marks after this time are 'late'
        );
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            class_id TEXT NOT NULL,
            date TEXT NOT NULL,          -- YYYY-MM-DD
            timestamp TEXT NOT NULL,     -- ISO datetime
            status TEXT NOT NULL DEFAULT 'present',
            note TEXT,
            UNIQUE (student_id, class_id, date),
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (class_id)   REFERENCES classes(id)  ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_att_class_date ON attendance(class_id, date);
        """
    )
    db.commit()
    db.close()


# --------------------------------------------------------------------------
# Utilities
# --------------------------------------------------------------------------
def require_key(fn):
    """Protect write routes when ATTENDANCE_API_KEY is configured."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if API_KEY and request.headers.get("X-API-Key") != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return fn(*args, **kwargs)
    return wrapper


def json_body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def parse_date(value, field="date"):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except (TypeError, ValueError):
        raise ValueError(f"'{field}' must be in YYYY-MM-DD format")


def ensure_student(db, student_id, name=None):
    db.execute("INSERT OR IGNORE INTO students (id, name) VALUES (?, ?)",
               (student_id, name or student_id))


def ensure_class(db, class_id, name=None):
    db.execute("INSERT OR IGNORE INTO classes (id, name) VALUES (?, ?)",
               (class_id, name or class_id))


def decide_status(db, class_id, requested, now):
    """Use the requested status, or auto-detect 'late' from the class cutoff."""
    if requested:
        requested = str(requested).lower()
        if requested not in VALID_STATUSES:
            raise ValueError(f"status must be one of {sorted(VALID_STATUSES)}")
        return requested
    row = db.execute("SELECT late_after FROM classes WHERE id = ?", (class_id,)).fetchone()
    if row and row["late_after"] and now.strftime("%H:%M") > row["late_after"]:
        return "late"
    return "present"


def record_attendance(db, student_id, class_id, status=None, day=None, note=None):
    """Insert one attendance row. Raises ValueError on bad input, KeyError on duplicate."""
    now = datetime.now()
    day = parse_date(day) if day else now.date().isoformat()
    ensure_student(db, student_id)
    ensure_class(db, class_id)
    status = decide_status(db, class_id, status, now)
    try:
        cur = db.execute(
            "INSERT INTO attendance (student_id, class_id, date, timestamp, status, note) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (student_id, class_id, day, now.isoformat(), status, note),
        )
    except sqlite3.IntegrityError:
        raise KeyError("Attendance already marked for this student, class and date")
    return {"id": cur.lastrowid, "student_id": student_id, "class_id": class_id,
            "date": day, "timestamp": now.isoformat(), "status": status}


def rows(cursor):
    return [dict(r) for r in cursor.fetchall()]


def validate_id(value, field):
    if not isinstance(value, (str, int)) or not str(value).strip():
        raise ValueError(f"'{field}' is required")
    return str(value).strip()


# --------------------------------------------------------------------------
# Students
# --------------------------------------------------------------------------
@app.route("/students", methods=["POST"])
@require_key
def add_student():
    data = json_body()
    try:
        sid = validate_id(data.get("student_id"), "student_id")
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    db = get_db()
    try:
        db.execute("INSERT INTO students (id, name, email) VALUES (?, ?, ?)",
                   (sid, data.get("name") or sid, data.get("email")))
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Student already exists"}), 409
    return jsonify({"message": "Student added", "student_id": sid}), 201


@app.route("/students", methods=["GET"])
def list_students():
    return jsonify(rows(get_db().execute("SELECT * FROM students ORDER BY id"))), 200


@app.route("/students/<student_id>", methods=["GET"])
def get_student(student_id):
    row = get_db().execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    return (jsonify(dict(row)), 200) if row else (jsonify({"error": "Student not found"}), 404)


@app.route("/students/<student_id>", methods=["PUT"])
@require_key
def update_student(student_id):
    data = json_body()
    db = get_db()
    cur = db.execute(
        "UPDATE students SET name = COALESCE(?, name), email = COALESCE(?, email) WHERE id = ?",
        (data.get("name"), data.get("email"), student_id))
    db.commit()
    return (jsonify({"message": "Student updated"}), 200) if cur.rowcount \
        else (jsonify({"error": "Student not found"}), 404)


@app.route("/students/<student_id>", methods=["DELETE"])
@require_key
def delete_student(student_id):
    db = get_db()
    cur = db.execute("DELETE FROM students WHERE id = ?", (student_id,))
    db.commit()
    return (jsonify({"message": "Student and their records deleted"}), 200) if cur.rowcount \
        else (jsonify({"error": "Student not found"}), 404)


# --------------------------------------------------------------------------
# Classes
# --------------------------------------------------------------------------
@app.route("/classes", methods=["POST"])
@require_key
def add_class():
    data = json_body()
    try:
        cid = validate_id(data.get("class_id"), "class_id")
        late_after = data.get("late_after")
        if late_after:
            datetime.strptime(late_after, "%H:%M")
    except ValueError as e:
        msg = str(e) if "required" in str(e) else "'late_after' must be HH:MM (24h)"
        return jsonify({"error": msg}), 400
    db = get_db()
    try:
        db.execute("INSERT INTO classes (id, name, teacher, late_after) VALUES (?, ?, ?, ?)",
                   (cid, data.get("name") or cid, data.get("teacher"), late_after))
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Class already exists"}), 409
    return jsonify({"message": "Class added", "class_id": cid}), 201


@app.route("/classes", methods=["GET"])
def list_classes():
    return jsonify(rows(get_db().execute("SELECT * FROM classes ORDER BY id"))), 200


@app.route("/classes/<class_id>", methods=["DELETE"])
@require_key
def delete_class(class_id):
    db = get_db()
    cur = db.execute("DELETE FROM classes WHERE id = ?", (class_id,))
    db.commit()
    return (jsonify({"message": "Class and its records deleted"}), 200) if cur.rowcount \
        else (jsonify({"error": "Class not found"}), 404)


# --------------------------------------------------------------------------
# Marking attendance
# --------------------------------------------------------------------------
@app.route("/mark_attendance", methods=["POST"])
@require_key
def mark_attendance():
    data = json_body()
    try:
        sid = validate_id(data.get("student_id"), "student_id")
        cid = validate_id(data.get("class_id"), "class_id")
    except ValueError:
        return jsonify({"error": "Invalid data"}), 400

    db = get_db()
    try:
        rec = record_attendance(db, sid, cid, data.get("status"), data.get("date"), data.get("note"))
        db.commit()
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except KeyError as e:
        return jsonify({"error": e.args[0]}), 409
    return jsonify({"message": "Attendance marked successfully",
                    "timestamp": rec["timestamp"], "record": rec}), 201


@app.route("/bulk_attendance", methods=["POST"])
@require_key
def bulk_attendance():
    """
    Body: {"class_id": "CS101", "date": "2026-10-08" (optional),
           "records": [{"student_id": "s1", "status": "present"}, ...]}
    """
    data = json_body()
    try:
        cid = validate_id(data.get("class_id"), "class_id")
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    records = data.get("records")
    if not isinstance(records, list) or not records:
        return jsonify({"error": "'records' must be a non-empty list"}), 400

    db = get_db()
    saved, skipped = [], []
    for item in records:
        try:
            sid = validate_id((item or {}).get("student_id"), "student_id")
            saved.append(record_attendance(db, sid, cid, item.get("status"),
                                           data.get("date"), item.get("note")))
        except (ValueError, KeyError, AttributeError) as e:
            reason = e.args[0] if e.args else "invalid record"
            skipped.append({"record": item, "reason": reason})
    db.commit()
    return jsonify({"saved": len(saved), "skipped": skipped}), 201 if saved else 400


@app.route("/attendance/<int:record_id>", methods=["PUT"])
@require_key
def update_attendance(record_id):
    data = json_body()
    status = data.get("status")
    if status and str(status).lower() not in VALID_STATUSES:
        return jsonify({"error": f"status must be one of {sorted(VALID_STATUSES)}"}), 400
    db = get_db()
    cur = db.execute(
        "UPDATE attendance SET status = COALESCE(?, status), note = COALESCE(?, note) WHERE id = ?",
        (status.lower() if status else None, data.get("note"), record_id))
    db.commit()
    return (jsonify({"message": "Record updated"}), 200) if cur.rowcount \
        else (jsonify({"error": "Record not found"}), 404)


@app.route("/attendance/<int:record_id>", methods=["DELETE"])
@require_key
def delete_attendance(record_id):
    db = get_db()
    cur = db.execute("DELETE FROM attendance WHERE id = ?", (record_id,))
    db.commit()
    return (jsonify({"message": "Record deleted"}), 200) if cur.rowcount \
        else (jsonify({"error": "Record not found"}), 404)


# --------------------------------------------------------------------------
# Viewing attendance
# --------------------------------------------------------------------------
def build_filters(class_id):
    """Shared filter builder: ?date= ?from= ?to= ?student_id= ?status="""
    clauses, params = ["class_id = ?"], [class_id]
    args = request.args
    if args.get("date"):
        clauses.append("date = ?"); params.append(parse_date(args["date"], "date"))
    if args.get("from"):
        clauses.append("date >= ?"); params.append(parse_date(args["from"], "from"))
    if args.get("to"):
        clauses.append("date <= ?"); params.append(parse_date(args["to"], "to"))
    if args.get("student_id"):
        clauses.append("student_id = ?"); params.append(args["student_id"])
    if args.get("status"):
        clauses.append("status = ?"); params.append(args["status"].lower())
    return " AND ".join(clauses), params


def class_exists(db, class_id):
    return db.execute("SELECT 1 FROM classes WHERE id = ?", (class_id,)).fetchone() is not None


@app.route("/attendance/<class_id>", methods=["GET"])
def get_attendance(class_id):
    db = get_db()
    if not class_exists(db, class_id):
        return jsonify({"error": "Class ID not found"}), 404
    try:
        where, params = build_filters(class_id)
        page = max(int(request.args.get("page", 1)), 1)
        per_page = min(max(int(request.args.get("per_page", 100)), 1), 500)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    total = db.execute(f"SELECT COUNT(*) FROM attendance WHERE {where}", params).fetchone()[0]
    data = rows(db.execute(
        f"SELECT * FROM attendance WHERE {where} ORDER BY date DESC, timestamp DESC "
        f"LIMIT ? OFFSET ?", params + [per_page, (page - 1) * per_page]))
    return jsonify({"class_id": class_id, "total": total, "page": page,
                    "per_page": per_page, "records": data}), 200


# --------------------------------------------------------------------------
# Reports
# --------------------------------------------------------------------------
def class_report(db, class_id):
    where, params = build_filters(class_id)
    sessions = db.execute(
        f"SELECT COUNT(DISTINCT date) FROM attendance WHERE {where}", params).fetchone()[0]
    report = {}
    for r in db.execute(
        f"""SELECT student_id,
                   COUNT(*) AS marked,
                   SUM(status = 'present')  AS present,
                   SUM(status = 'late')     AS late,
                   SUM(status = 'absent')   AS absent,
                   SUM(status = 'excused')  AS excused
            FROM attendance WHERE {where} GROUP BY student_id""", params):
        attended = r["present"] + r["late"]            # late still counts as attending
        denom = sessions - r["excused"]                # excused days don't count against
        report[r["student_id"]] = {
            "marked": r["marked"], "present": r["present"], "late": r["late"],
            "absent": r["absent"], "excused": r["excused"],
            "attendance_percent": round(100 * attended / denom, 1) if denom > 0 else None,
        }
    return sessions, report


@app.route("/attendance_report", methods=["GET"])
def attendance_report():
    class_id = request.args.get("class_id")
    db = get_db()
    if not class_id or not class_exists(db, class_id):
        return jsonify({"error": "Class ID not found"}), 404
    try:
        sessions, report = class_report(db, class_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"class_id": class_id, "total_sessions": sessions, "students": report}), 200


@app.route("/student_report/<student_id>", methods=["GET"])
def student_report(student_id):
    db = get_db()
    if not db.execute("SELECT 1 FROM students WHERE id = ?", (student_id,)).fetchone():
        return jsonify({"error": "Student not found"}), 404
    out = {}
    for c in db.execute("SELECT DISTINCT class_id FROM attendance WHERE student_id = ?", (student_id,)):
        cid = c["class_id"]
        sessions = db.execute("SELECT COUNT(DISTINCT date) FROM attendance WHERE class_id = ?",
                              (cid,)).fetchone()[0]
        counts = {s: 0 for s in VALID_STATUSES}
        for r in db.execute("SELECT status, COUNT(*) n FROM attendance "
                            "WHERE student_id = ? AND class_id = ? GROUP BY status", (student_id, cid)):
            counts[r["status"]] = r["n"]
        denom = sessions - counts["excused"]
        out[cid] = {**counts, "total_sessions": sessions,
                    "attendance_percent": round(100 * (counts["present"] + counts["late"]) / denom, 1)
                    if denom > 0 else None}
    return jsonify({"student_id": student_id, "classes": out}), 200


@app.route("/low_attendance", methods=["GET"])
def low_attendance():
    """Students under ?threshold= (default 75%) in ?class_id=."""
    class_id = request.args.get("class_id")
    db = get_db()
    if not class_id or not class_exists(db, class_id):
        return jsonify({"error": "Class ID not found"}), 404
    try:
        threshold = float(request.args.get("threshold", 75))
        sessions, report = class_report(db, class_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    flagged = {sid: r for sid, r in report.items()
               if r["attendance_percent"] is not None and r["attendance_percent"] < threshold}
    return jsonify({"class_id": class_id, "threshold": threshold, "flagged": flagged}), 200


@app.route("/export/<class_id>", methods=["GET"])
def export_csv(class_id):
    db = get_db()
    if not class_exists(db, class_id):
        return jsonify({"error": "Class ID not found"}), 404
    try:
        where, params = build_filters(class_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "student_id", "class_id", "date", "timestamp", "status", "note"])
    for r in db.execute(f"SELECT id, student_id, class_id, date, timestamp, status, note "
                        f"FROM attendance WHERE {where} ORDER BY date, student_id", params):
        writer.writerow(list(r))
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={class_id}_attendance.csv"})


# --------------------------------------------------------------------------
# Misc / errors
# --------------------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()}), 200


@app.errorhandler(404)
def not_found(_e):
    return jsonify({"error": "Route not found"}), 404


@app.errorhandler(405)
def bad_method(_e):
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(500)
def server_error(_e):
    return jsonify({"error": "Internal server error"}), 500


init_db()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")