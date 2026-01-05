import sqlite3
from flask import Flask, render_template

app = Flask(__name__)

# init database, create database if not exists and insert one sample row
def init_db():
    with sqlite3.connect("database.db") as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")
        # insert one sample row
        cursor = conn.cursor()
        if not cursor.execute("SELECT * FROM users").fetchone():
            conn.execute("INSERT INTO users (name) VALUES ('liuyujia')")
        conn.commit()

@app.route('/')
def index():
    # fetch data from sqlite
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM users")
        user_name = cursor.fetchone()[0]
    return render_template("index.html", name=user_name)

if __name__ == '__main__':
    init_db()
    print("local server running on: http://127.0.0.1:5000")
    app.run(debug=True)
