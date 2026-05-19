from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3, os
from datetime import date

app = Flask(__name__)
app.secret_key = 'blood_bank_secret_2026'

DB = os.path.join(os.path.dirname(__file__), 'blood_bank.db')

# ─── Database helpers ────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    c = db.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS tb_donor (
        D_id INTEGER PRIMARY KEY AUTOINCREMENT,
        D_name TEXT, D_bloodtype TEXT, D_age INTEGER,
        D_gender TEXT, D_identification TEXT, D_medical TEXT,
        D_contact TEXT, D_email TEXT, D_address TEXT, D_Last_Donation TEXT
    );

    CREATE TABLE IF NOT EXISTS tb_hospital (
        H_id INTEGER PRIMARY KEY AUTOINCREMENT,
        H_name TEXT, H_contact TEXT, H_email TEXT,
        H_address TEXT, H_con_person TEXT, password TEXT
    );

    CREATE TABLE IF NOT EXISTS blood_inventory (
        BloodId INTEGER PRIMARY KEY AUTOINCREMENT,
        BloodType TEXT, Quantity INTEGER, EntryDate TEXT,
        status TEXT DEFAULT 'Available'
    );

    CREATE TABLE IF NOT EXISTS tb_h_request (
        H_R_id INTEGER PRIMARY KEY AUTOINCREMENT,
        H_id INTEGER, H_R_BloodGrp TEXT, Requested_qnt INTEGER,
        Fulfill_till TEXT, status TEXT DEFAULT 'Pending'
    );
    """)

    # Seed data only if empty
    if not c.execute("SELECT 1 FROM admins").fetchone():
        c.execute("INSERT INTO admins (username,password) VALUES ('admin','admin123')")

    if not c.execute("SELECT 1 FROM tb_donor").fetchone():
        donors = [
            ("Arjun Sharma","O+",28,"Male","AADH001","None","9876543210","arjun@email.com","Bilaspur, CG","2026-03-10"),
            ("Priya Patel","A+",34,"Female","AADH002","None","9812345678","priya@email.com","Raipur, CG","2026-01-22"),
            ("Rahul Singh","B+",41,"Male","AADH003","None","9898765432","rahul@email.com","Durg, CG","2025-12-05"),
        ]
        c.executemany("INSERT INTO tb_donor VALUES (NULL,?,?,?,?,?,?,?,?,?,?)", donors)

    if not c.execute("SELECT 1 FROM tb_hospital").fetchone():
        hospitals = [
            ("City General Hospital","9876543210","city@hosp.in","Bilaspur, CG","Dr. Sharma","hosp123"),
            ("Apollo Medical Center","9812345678","apollo@med.in","Raipur, CG","Dr. Patel","hosp123"),
            ("Sunrise Clinic","9898765432","sunrise@cl.in","Durg, CG","Dr. Singh","hosp123"),
        ]
        c.executemany("INSERT INTO tb_hospital VALUES (NULL,?,?,?,?,?,?)", hospitals)

    if not c.execute("SELECT 1 FROM blood_inventory").fetchone():
        inventory = [
            ("A+",85,"2026-05-01","Available"),("A-",32,"2026-05-01","Available"),
            ("B+",70,"2026-05-01","Available"),("B-",18,"2026-05-01","Low Stock"),
            ("O+",95,"2026-05-01","Available"),("O-",40,"2026-05-01","Available"),
            ("AB+",55,"2026-05-01","Available"),("AB-",12,"2026-04-28","Low Stock"),
        ]
        c.executemany("INSERT INTO blood_inventory VALUES (NULL,?,?,?,?)", inventory)

    if not c.execute("SELECT 1 FROM tb_h_request").fetchone():
        c.executemany("INSERT INTO tb_h_request VALUES (NULL,?,?,?,?,?)", [
            (1,"O+",10,"2026-05-20","Pending"),
            (2,"A+",5,"2026-05-18","Approved"),
            (3,"B-",3,"2026-05-22","Pending"),
        ])

    db.commit()
    db.close()

# ─── Auth guards ─────────────────────────────────────────────────────────────

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def hospital_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'hospital':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─── Public routes ────────────────────────────────────────────────────────────

@app.route('/')
def index():
    db = get_db()
    donors  = db.execute("SELECT COUNT(*) as c FROM tb_donor").fetchone()['c']
    hosps   = db.execute("SELECT COUNT(*) as c FROM tb_hospital").fetchone()['c']
    units   = db.execute("SELECT SUM(Quantity) as c FROM blood_inventory").fetchone()['c'] or 0
    inv     = db.execute("SELECT * FROM blood_inventory ORDER BY BloodType").fetchall()
    db.close()
    return render_template('index.html', donors=donors, hosps=hosps, units=units, inventory=inv)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/login', methods=['GET','POST'])
def login():
    error = ''
    login_type = request.form.get('login_type', request.args.get('tab','admin'))
    if request.method == 'POST':
        login_type = request.form.get('login_type','admin')
        db = get_db()
        if login_type == 'admin':
            username = request.form.get('username','').strip()
            password = request.form.get('password','').strip()
            row = db.execute("SELECT * FROM admins WHERE username=? AND password=?", (username, password)).fetchone()
            if row:
                session['admin_id'] = row['id']
                session['admin_username'] = row['username']
                session['role'] = 'admin'
                db.close()
                return redirect(url_for('admin_dashboard'))
            error = "Invalid username or password."
        else:
            email    = request.form.get('email','').strip()
            password = request.form.get('password','').strip()
            row = db.execute("SELECT * FROM tb_hospital WHERE H_email=? AND password=?", (email, password)).fetchone()
            if row:
                session['hospital_id']   = row['H_id']
                session['hospital_name'] = row['H_name']
                session['role'] = 'hospital'
                db.close()
                return redirect(url_for('hospital_request'))
            error = "Invalid email or password."
        db.close()
    return render_template('login.html', error=error, login_type=login_type)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ─── Admin routes ─────────────────────────────────────────────────────────────

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    db = get_db()
    donors  = db.execute("SELECT COUNT(*) as c FROM tb_donor").fetchone()['c']
    hosps   = db.execute("SELECT COUNT(*) as c FROM tb_hospital").fetchone()['c']
    units   = db.execute("SELECT SUM(Quantity) as c FROM blood_inventory").fetchone()['c'] or 0
    pending = db.execute("SELECT COUNT(*) as c FROM tb_h_request WHERE status='Pending'").fetchone()['c']
    inv     = db.execute("SELECT BloodType, Quantity, status FROM blood_inventory ORDER BY BloodType").fetchall()
    recent  = db.execute("""SELECT r.*, h.H_name FROM tb_h_request r
                            JOIN tb_hospital h ON r.H_id=h.H_id
                            ORDER BY r.H_R_id DESC LIMIT 5""").fetchall()
    db.close()
    return render_template('admin/dashboard.html',
                           donors=donors, hosps=hosps, units=units,
                           pending=pending, inventory=inv, recent=recent)

# ── Donors ──
@app.route('/admin/donors')
@admin_required
def admin_donors():
    msg = request.args.get('msg','')
    db  = get_db()
    donors = db.execute("SELECT * FROM tb_donor ORDER BY D_id DESC").fetchall()
    db.close()
    return render_template('admin/donors.html', donors=donors, msg=msg)

@app.route('/admin/register_donor', methods=['GET','POST'])
@admin_required
def register_donor():
    error = ''
    if request.method == 'POST':
        f = request.form
        name   = f.get('name','').strip()
        blood  = f.get('blood_type','')
        age    = f.get('age','0')
        gender = f.get('gender','')
        id_proof = f.get('id_proof','').strip()
        medical  = f.get('medical','').strip()
        contact  = f.get('contact','').strip()
        email    = f.get('email','').strip()
        address  = f.get('address','').strip()
        last_don = f.get('last_donation','')
        if name and blood and age and gender and contact:
            db = get_db()
            db.execute("INSERT INTO tb_donor VALUES (NULL,?,?,?,?,?,?,?,?,?,?)",
                       (name, blood, int(age), gender, id_proof, medical, contact, email, address, last_don))
            db.commit(); db.close()
            return redirect(url_for('admin_donors', msg='added'))
        error = "Please fill all required fields."
    return render_template('admin/register_donor.html', error=error)

@app.route('/admin/edit_donor/<int:did>', methods=['GET','POST'])
@admin_required
def edit_donor(did):
    db = get_db()
    error = ''
    if request.method == 'POST':
        f = request.form
        db.execute("""UPDATE tb_donor SET D_name=?,D_bloodtype=?,D_age=?,D_gender=?,
                      D_identification=?,D_medical=?,D_contact=?,D_email=?,D_address=?,D_Last_Donation=?
                      WHERE D_id=?""",
                   (f['name'],f['blood_type'],int(f['age']),f['gender'],f['id_proof'],
                    f['medical'],f['contact'],f['email'],f['address'],f['last_donation'],did))
        db.commit(); db.close()
        return redirect(url_for('admin_donors', msg='updated'))
    donor = db.execute("SELECT * FROM tb_donor WHERE D_id=?", (did,)).fetchone()
    db.close()
    if not donor: return redirect(url_for('admin_donors'))
    return render_template('admin/edit_donor.html', donor=donor, error=error)

@app.route('/admin/delete_donor/<int:did>')
@admin_required
def delete_donor(did):
    db = get_db()
    db.execute("DELETE FROM tb_donor WHERE D_id=?", (did,))
    db.commit(); db.close()
    return redirect(url_for('admin_donors', msg='deleted'))

# ── Hospitals ──
@app.route('/admin/hospitals')
@admin_required
def admin_hospitals():
    msg = request.args.get('msg','')
    db  = get_db()
    hospitals = db.execute("SELECT * FROM tb_hospital ORDER BY H_id DESC").fetchall()
    db.close()
    return render_template('admin/hospitals.html', hospitals=hospitals, msg=msg)

@app.route('/admin/register_hospital', methods=['GET','POST'])
@admin_required
def register_hospital():
    error = ''
    if request.method == 'POST':
        f = request.form
        name    = f.get('name','').strip()
        contact = f.get('contact','').strip()
        email   = f.get('email','').strip()
        address = f.get('address','').strip()
        person  = f.get('contact_person','').strip()
        password= f.get('password','').strip()
        if name and contact and email and password:
            db = get_db()
            db.execute("INSERT INTO tb_hospital VALUES (NULL,?,?,?,?,?,?)",
                       (name, contact, email, address, person, password))
            db.commit(); db.close()
            return redirect(url_for('admin_hospitals', msg='registered'))
        error = "Please fill all required fields."
    return render_template('admin/register_hospital.html', error=error)

@app.route('/admin/edit_hospital/<int:hid>', methods=['GET','POST'])
@admin_required
def edit_hospital(hid):
    db = get_db()
    error = ''
    if request.method == 'POST':
        f = request.form
        db.execute("""UPDATE tb_hospital SET H_name=?,H_contact=?,H_email=?,
                      H_address=?,H_con_person=?,password=? WHERE H_id=?""",
                   (f['name'],f['contact'],f['email'],f['address'],f['contact_person'],f['password'],hid))
        db.commit(); db.close()
        return redirect(url_for('admin_hospitals', msg='updated'))
    hospital = db.execute("SELECT * FROM tb_hospital WHERE H_id=?", (hid,)).fetchone()
    db.close()
    if not hospital: return redirect(url_for('admin_hospitals'))
    return render_template('admin/edit_hospital.html', hospital=hospital, error=error)

@app.route('/admin/delete_hospital/<int:hid>')
@admin_required
def delete_hospital(hid):
    db = get_db()
    db.execute("DELETE FROM tb_hospital WHERE H_id=?", (hid,))
    db.commit(); db.close()
    return redirect(url_for('admin_hospitals', msg='deleted'))

# ── Inventory ──
@app.route('/admin/inventory')
@admin_required
def admin_inventory():
    msg = request.args.get('msg','')
    db  = get_db()
    inventory = db.execute("SELECT * FROM blood_inventory ORDER BY BloodType").fetchall()
    db.close()
    return render_template('admin/inventory.html', inventory=inventory, msg=msg)

@app.route('/admin/add_inventory', methods=['GET','POST'])
@admin_required
def add_inventory():
    error = ''
    if request.method == 'POST':
        blood  = request.form.get('blood_type','')
        qty    = request.form.get('quantity','0')
        edate  = request.form.get('entry_date', str(date.today()))
        if blood and int(qty) > 0:
            status = 'Low Stock' if int(qty) < 20 else 'Available'
            db = get_db()
            db.execute("INSERT INTO blood_inventory VALUES (NULL,?,?,?,?)",
                       (blood, int(qty), edate, status))
            db.commit(); db.close()
            return redirect(url_for('admin_inventory', msg='added'))
        error = "Please fill all required fields."
    return render_template('admin/add_inventory.html', error=error, today=str(date.today()))

@app.route('/admin/edit_inventory/<int:bid>', methods=['GET','POST'])
@admin_required
def edit_inventory(bid):
    db = get_db()
    error = ''
    if request.method == 'POST':
        qty   = int(request.form.get('quantity', 0))
        edate = request.form.get('entry_date', str(date.today()))
        status = 'Low Stock' if qty < 20 else 'Available'
        db.execute("UPDATE blood_inventory SET Quantity=?,EntryDate=?,status=? WHERE BloodId=?",
                   (qty, edate, status, bid))
        db.commit(); db.close()
        return redirect(url_for('admin_inventory', msg='updated'))
    item = db.execute("SELECT * FROM blood_inventory WHERE BloodId=?", (bid,)).fetchone()
    db.close()
    if not item: return redirect(url_for('admin_inventory'))
    return render_template('admin/edit_inventory.html', item=item, error=error)

@app.route('/admin/delete_inventory/<int:bid>')
@admin_required
def delete_inventory(bid):
    db = get_db()
    db.execute("DELETE FROM blood_inventory WHERE BloodId=?", (bid,))
    db.commit(); db.close()
    return redirect(url_for('admin_inventory', msg='deleted'))

# ── Requests ──
@app.route('/admin/requests')
@admin_required
def admin_requests():
    msg = request.args.get('msg','')
    db  = get_db()
    requests_ = db.execute("""SELECT r.*, h.H_name FROM tb_h_request r
                              JOIN tb_hospital h ON r.H_id=h.H_id
                              ORDER BY r.H_R_id DESC""").fetchall()
    db.close()
    return render_template('admin/requests.html', requests=requests_, msg=msg)

@app.route('/admin/approve_request/<int:rid>')
@admin_required
def approve_request(rid):
    db  = get_db()
    req = db.execute("SELECT * FROM tb_h_request WHERE H_R_id=?", (rid,)).fetchone()
    if req:
        blood = req['H_R_BloodGrp']; qty = req['Requested_qnt']
        inv = db.execute("SELECT * FROM blood_inventory WHERE BloodType=?", (blood,)).fetchone()
        if inv and inv['Quantity'] >= qty:
            new_qty = inv['Quantity'] - qty
            new_status = 'Low Stock' if new_qty < 20 else 'Available'
            db.execute("UPDATE blood_inventory SET Quantity=?,status=? WHERE BloodType=?",
                       (new_qty, new_status, blood))
            db.execute("UPDATE tb_h_request SET status='Approved' WHERE H_R_id=?", (rid,))
            db.commit(); db.close()
            return redirect(url_for('admin_requests', msg='approved'))
        db.close()
        return redirect(url_for('admin_requests', msg='insufficient'))
    db.close()
    return redirect(url_for('admin_requests'))

@app.route('/admin/delete_request/<int:rid>')
@admin_required
def delete_request(rid):
    db = get_db()
    db.execute("DELETE FROM tb_h_request WHERE H_R_id=?", (rid,))
    db.commit(); db.close()
    return redirect(url_for('admin_requests', msg='deleted'))

# ─── Hospital routes ──────────────────────────────────────────────────────────

@app.route('/hospital/request', methods=['GET','POST'])
@hospital_required
def hospital_request():
    h_id  = session['hospital_id']
    error = success = ''
    db    = get_db()
    if request.method == 'POST':
        blood = request.form.get('blood_type','')
        qty   = int(request.form.get('quantity', 0))
        till  = request.form.get('fulfill_till','')
        if blood and qty > 0 and till:
            inv = db.execute("SELECT Quantity FROM blood_inventory WHERE BloodType=?", (blood,)).fetchone()
            if not inv or inv['Quantity'] < qty:
                error = f"Requested quantity exceeds available stock for {blood}. Available: {inv['Quantity'] if inv else 0} units."
            else:
                db.execute("INSERT INTO tb_h_request VALUES (NULL,?,?,?,?,'Pending')",
                           (h_id, blood, qty, till))
                db.commit()
                success = "Blood request submitted successfully! Awaiting admin approval."
        else:
            error = "Please fill all required fields."
    inventory = db.execute("SELECT BloodType, Quantity, status FROM blood_inventory ORDER BY BloodType").fetchall()
    db.close()
    return render_template('hospital/request.html',
                           inventory=inventory, error=error, success=success,
                           today=str(date.today()))

@app.route('/hospital/my_requests')
@hospital_required
def hospital_my_requests():
    h_id = session['hospital_id']
    db   = get_db()
    reqs = db.execute("""SELECT r.*, h.H_name FROM tb_h_request r
                         JOIN tb_hospital h ON r.H_id=h.H_id
                         WHERE r.H_id=? ORDER BY r.H_R_id DESC""", (h_id,)).fetchall()
    db.close()
    return render_template('hospital/my_requests.html', requests=reqs)

@app.route('/hospital/availability')
@hospital_required
def hospital_availability():
    db  = get_db()
    inv = db.execute("SELECT * FROM blood_inventory ORDER BY BloodType").fetchall()
    db.close()
    return render_template('hospital/availability.html', inventory=inv)

# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    print("\n🩸 Blood Bank Management System")
    print("   Running at: http://localhost:5000")
    print("\n   Admin    → username: admin   | password: admin123")
    print("   Hospital → email: city@hosp.in | password: hosp123\n")
    app.run(debug=True, port=5000)
