from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

conn = get_db_connection()
conn.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    m1 INTEGER,
    m2 INTEGER,
    m3 INTEGER,
    total INTEGER,
    average REAL,
    result TEXT
)
""")
conn.commit()
conn.close()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form["name"]
        m1 = int(request.form["m1"])
        m2 = int(request.form["m2"])
        m3 = int(request.form["m3"])

        total = m1 + m2 + m3
        average = total / 3
        result = "Pass" if average >= 40 else "Fail"

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO students (name, m1, m2, m3, total, average, result) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, m1, m2, m3, total, average, result),
        )
        conn.commit()
        conn.close()

    return render_template("index.html")

@app.route("/results")
def results():
    conn = get_db_connection()
    students = conn.execute("SELECT * FROM students").fetchall()
    conn.close()
    return render_template("results.html", students=students)

if __name__ == "__main__":
    app.run(debug=True)
