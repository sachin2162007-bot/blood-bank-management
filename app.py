from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

# ---------- DATABASE ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "blood_bank.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ---------- INIT DATABASE ----------
def init_db():
    db = get_db()
    cursor = db.cursor()

    # Admins
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    """)

    # Patients
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            blood_group TEXT,
            phone TEXT,
            status TEXT
        )
    """)

    # Donors
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS donors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            dob TEXT,
            gender TEXT,
            blood_group TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            weight TEXT,
            last_donation TEXT,
            medications TEXT,
            conditions TEXT,
            tattoo TEXT,
            donation_date TEXT,
            donation_center TEXT,
            frequency TEXT,
            consent INTEGER
        )
    """)

    # Blood stock
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blood_stock (
            blood_group TEXT PRIMARY KEY,
            units INTEGER
        )
    """)

    db.commit()
    db.close()

# ---------- DEFAULT ADMIN ----------
def create_default_admin():
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM admins WHERE username = ?",
        ("admin",)
    )
    admin = cursor.fetchone()

    if not admin:
        cursor.execute(
            "INSERT INTO admins (username, password) VALUES (?, ?)",
            ("admin", "admin123")
        )
        db.commit()

    db.close()

# Run DB setup
init_db()
create_default_admin()

# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("index.html")

# ---------- ADMIN LOGIN ----------
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM admins WHERE username=? AND password=?",
            (username, password)
        )
        admin = cursor.fetchone()
        db.close()

        if admin:
            return redirect(url_for("admin_dashboard"))
        else:
            return "Invalid Admin Username or Password"

    return render_template("admin_login.html")

# ---------- ADMIN DASHBOARD ----------
@app.route("/admin/dashboard")
def admin_dashboard():
    return render_template("admin_dashboard.html")

# ---------- VIEW DONORS ----------
@app.route("/admin/donors")
def view_donors():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM donors")
    donors = cursor.fetchall()
    db.close()
    return render_template("view_donors.html", donors=donors)

# ---------- VIEW PATIENTS ----------
@app.route("/admin/patients")
def view_patients():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM patients")
    patients = cursor.fetchall()
    db.close()
    return render_template("view_patients.html", patients=patients)

# ---------- APPROVE PATIENT ----------
@app.route("/admin/approve/<int:pid>")
def approve_patient(pid):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT blood_group FROM patients WHERE id=?", (pid,))
    result = cursor.fetchone()

    if result:
        blood_group = result["blood_group"]

        cursor.execute(
            "SELECT units FROM blood_stock WHERE blood_group=?",
            (blood_group,)
        )
        stock = cursor.fetchone()

        if stock and stock["units"] > 0:
            cursor.execute(
                "UPDATE blood_stock SET units = units - 1 WHERE blood_group=?",
                (blood_group,)
            )
            cursor.execute(
                "UPDATE patients SET status='Approved' WHERE id=?",
                (pid,)
            )
            db.commit()

    db.close()
    return redirect(url_for("view_patients"))

# ---------- MANAGE BLOOD STOCK ----------
@app.route("/admin/stock", methods=["GET", "POST"])
def manage_stock():
    db = get_db()
    cursor = db.cursor()

    if request.method == "POST":
        blood_group = request.form["blood_group"]
        units = int(request.form["units"])

        cursor.execute(
            "INSERT OR REPLACE INTO blood_stock (blood_group, units) VALUES (?, ?)",
            (blood_group, units)
        )
        db.commit()

    cursor.execute("SELECT * FROM blood_stock")
    stock = cursor.fetchall()
    db.close()
    return render_template("blood_stock.html", stock=stock)

# ---------- DONOR REGISTER ----------
@app.route("/donor/register", methods=["GET", "POST"])
def donor_register():
    if request.method == "POST":
        data = request.form
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO donors (
                full_name, dob, gender, blood_group, phone, email, address,
                weight, last_donation, medications, conditions, tattoo,
                donation_date, donation_center, frequency, consent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("full_name"),
            data.get("dob"),
            data.get("gender"),
            data.get("blood_group"),
            data.get("phone"),
            data.get("email"),
            data.get("address"),
            data.get("weight"),
            data.get("last_donation"),
            data.get("medications"),
            data.get("conditions"),
            data.get("tattoo"),
            data.get("donation_date"),
            data.get("donation_center"),
            data.get("frequency"),
            1 if data.get("consent") else 0
        ))

        db.commit()
        db.close()
        return redirect("/")

    return render_template("donor_register.html")

# ---------- PATIENT REQUEST ----------
@app.route("/patient/request", methods=["GET", "POST"])
def patient_request():
    if request.method == "POST":
        name = request.form["name"]
        blood_group = request.form["blood_group"]
        phone = request.form["phone"]

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO patients (name, blood_group, phone, status) VALUES (?, ?, ?, ?)",
            (name, blood_group, phone, "Pending")
        )
        db.commit()
        db.close()

        return "Blood request submitted successfully"

    return render_template("patient_request.html")

# ---------- RUN ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)