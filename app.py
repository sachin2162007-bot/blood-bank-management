from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import os
print("FLASK RUNNING FROM:", os.getcwd())

app = Flask(__name__)

# ---------- DATABASE CONNECTION ----------
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="blood_user",
        password="blood123",
        database="blood_bank_db"
    )


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
            "SELECT * FROM admin WHERE username=%s AND password=%s",
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

# ---------- VIEW DONORS (FIXED 404) ----------
@app.route("/admin/donors")
def view_donors():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
    SELECT id, full_name, blood_group, phone
    FROM donors
""")

    donors = cursor.fetchall()
    db.close()

    return render_template("view_donors.html", donors=donors)

# ---------- VIEW PATIENT REQUESTS ----------
@app.route("/admin/patients")
def view_patients():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
    SELECT id, name, blood_group, phone, status
    FROM patients
""")

    patients = cursor.fetchall()
    db.close()

    return render_template("view_patients.html", patients=patients)

# ---------- APPROVE PATIENT ----------
@app.route("/admin/approve/<int:pid>")
def approve_patient(pid):
    db = get_db()
    cursor = db.cursor()

    # 1. Get patient's blood group
    cursor.execute(
        "SELECT blood_group FROM patients WHERE id=%s",
        (pid,)
    )
    result = cursor.fetchone()

    if not result:
        db.close()
        return redirect(url_for("view_patients"))

    blood_group = result[0]

    # 2. Check available stock
    cursor.execute(
        "SELECT units FROM blood_stock WHERE blood_group=%s",
        (blood_group,)
    )
    stock = cursor.fetchone()

    if stock and stock[0] > 0:
        # 3. Reduce stock by 1
        cursor.execute(
            "UPDATE blood_stock SET units = units - 1 WHERE blood_group=%s",
            (blood_group,)
        )

        # 4. Approve patient
        cursor.execute(
            "UPDATE patients SET status='Approved' WHERE id=%s",
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
        units = request.form["units"]

        cursor.execute("""
            INSERT INTO blood_stock (blood_group, units)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE units=%s
        """, (blood_group, units, units))
        db.commit()

    cursor.execute("SELECT * FROM blood_stock")
    stock = cursor.fetchall()
    db.close()

    return render_template("blood_stock.html", stock=stock)

# ---------- VIEW BLOOD STOCK ----------
@app.route("/admin/view-stock")
def view_blood_stock():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM blood_stock")
    stock = cursor.fetchall()
    db.close()

    return render_template("view_blood_stock.html", stock=stock)
@app.route("/donor/register", methods=["GET", "POST"])
def donor_register():
    if request.method == "POST":
        data = request.form

        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
    INSERT INTO donors 
    (
        full_name, dob, gender, blood_group, phone, email, address,
        weight, last_donation, medications, conditions, tattoo,
        donation_date, donation_center, frequency, consent
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
@app.route("/patient/request", methods=["GET", "POST"])
def patient_request():
    if request.method == "POST":
        name = request.form["name"]
        blood_group = request.form["blood_group"]
        phone = request.form["phone"]

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
    "INSERT INTO patients (name, blood_group, phone) VALUES (%s, %s, %s)",
    (name, blood_group, phone)
)


        db.commit()
        db.close()

        return "Blood request submitted successfully!"

    return render_template("patient_request.html")

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
