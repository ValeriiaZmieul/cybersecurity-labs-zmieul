from flask import Flask, request, jsonify
import sqlite3
import os
import threading
import time
import sys

# Зберігаємо базу поруч із файлом скрипта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "students.db")

def init_db(path=DB_PATH, force=False):
    print(f"Створення БД за шляхом: {path}")

    if os.path.exists(path) and not force:
        print("База вже існує — створення пропущено.")
        return

    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL,
            group_name TEXT
        );
    """)

    students = [
        ("Валерія", "Змєул", "valeriia.zmieul@hneu.net", "CS-1"),
        ("Іван", "Петренко", "ivan.petrenko@example.com", "CS-1"),
        ("Олена", "Коваль", "olena.koval@example.com", "CS-2"),
        ("Марко", "Іванов", "marko.ivanov@example.com", "CS-2"),
    ]
    c.executemany(
        "INSERT INTO students (first_name, last_name, email, group_name) VALUES (?, ?, ?, ?);",
        students
    )
    conn.commit()
    conn.close()
    print("Базу створено та заповнено.")

def vulnerable_search_db(search_term, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    query = (
        "SELECT id, first_name, last_name, email, group_name FROM students "
        "WHERE last_name LIKE '%" + search_term + "%';"
    )
    try:
        c.execute(query)
        rows = c.fetchall()
    except Exception as e:
        rows = []
        conn.close()
        return {"query": query, "error": str(e), "rows": rows}
    conn.close()
    return {"query": query, "rows": rows}


def safe_search_db(search_term, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    query = "SELECT id, first_name, last_name, email, group_name FROM students WHERE last_name LIKE ?;"
    try:
        pattern = f"%{search_term}%"
        c.execute(query, (pattern,))
        rows = c.fetchall()
    except Exception as e:
        rows = []
        conn.close()
        return {"query": query, "error": str(e), "rows": rows}
    conn.close()
    return {"query": query, "rows": rows}


app = Flask(__name__)

@app.route("/vulnerable_search", methods=["GET"])
def vulnerable_search_endpoint():
    q = request.args.get("q", "")
    result = vulnerable_search_db(q)
    rows = [{"id": r[0], "first_name": r[1], "last_name": r[2],
             "email": r[3], "group": r[4]} for r in result.get("rows", [])]
    return jsonify({"query": result.get("query"), "rows": rows})


@app.route("/safe_search", methods=["GET"])
def safe_search_endpoint():
    q = request.args.get("q", "")
    result = safe_search_db(q)
    rows = [{"id": r[0], "first_name": r[1], "last_name": r[2],
             "email": r[3], "group": r[4]} for r in result.get("rows", [])]
    return jsonify({"query": result.get("query"), "rows": rows})


if __name__ == "__main__":
    init_db(force=False)
    app.run(port=5001)