from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import qrcode
import os

app = Flask(__name__)

DB_FILE = 'database.db'
QR_DIR = 'static/qrcodes'

# Make QR directory if it doesn't exist
if not os.path.exists(QR_DIR):
    os.makedirs(QR_DIR)

# Initialize database if not exists
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS person (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gatepass_number TEXT UNIQUE,
                name TEXT,
                company TEXT,
                department TEXT,
                emergency_contact TEXT,
                site_incharge TEXT,
                blood_group TEXT,
                last_training_name TEXT,
                last_training_attended TEXT
            )
        ''')

@app.route('/')
def home():
    return redirect(url_for('start'))

@app.route('/start', methods=['GET', 'POST'])
def start():
    if request.method == 'POST':
        gatepass_number = request.form.get('gatepass_number', '').strip()
        if not gatepass_number:
            return render_template('start.html', error="Gatepass number cannot be empty.")
        # Replace / with _ so it can safely be part of the URL
        safe_gatepass = gatepass_number.replace('/', '_')
        return redirect(url_for('register', gatepass_number=safe_gatepass))
    return render_template('start.html')

@app.route('/register/<gatepass_number>', methods=['GET', 'POST'])
def register(gatepass_number):
    # Convert back _ to / for real gatepass
    real_gatepass = gatepass_number.replace('_', '/')
    person = None

    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM person WHERE gatepass_number = ?", (real_gatepass,))
        person = cur.fetchone()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        company = request.form.get('company', '').strip()
        department = request.form.get('department', '').strip()
        emergency_contact = request.form.get('emergency_contact', '').strip()
        site_incharge = request.form.get('site_incharge', '').strip()
        blood_group = request.form.get('blood_group', '').strip()
        last_training_name = request.form.get('last_training_name', '').strip()
        last_training_attended = request.form.get('last_training_attended', '').strip()

        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            if person:
                # Update existing
                cur.execute('''
                    UPDATE person SET name=?, company=?, department=?, emergency_contact=?, 
                    site_incharge=?, blood_group=?, last_training_name=?, last_training_attended=?
                    WHERE gatepass_number=?
                ''', (name, company, department, emergency_contact, site_incharge, blood_group, last_training_name, last_training_attended, real_gatepass))
                person_id = person[0]
            else:
                # Insert new
                cur.execute('''
                    INSERT INTO person (gatepass_number, name, company, department, emergency_contact, 
                    site_incharge, blood_group, last_training_name, last_training_attended)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (real_gatepass, name, company, department, emergency_contact, site_incharge, blood_group, last_training_name, last_training_attended))
                person_id = cur.lastrowid

                # Generate QR once
                profile_url = request.host_url.rstrip('/') + '/profile/' + str(person_id)
                qr_img = qrcode.make(profile_url)
                qr_filename = f"person_{person_id}.png"
                qr_path = f"{QR_DIR}/{qr_filename}"
                qr_img.save(qr_path)

            conn.commit()

        # For display: use url_for so browser can see static file
        qr_filename = f"person_{person_id}.png"
        profile_url = request.host_url.rstrip('/') + '/profile/' + str(person_id)
        return render_template('qr_generated.html', qr_filename=qr_filename, profile_url=profile_url)

    return render_template('register.html', person=person, gatepass_number=real_gatepass)

@app.route('/profile/<int:person_id>')
def profile(person_id):
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM person WHERE id = ?", (person_id,))
        person = cur.fetchone()
    if not person:
        return "Profile not found.", 404
    return render_template('profile.html', person=person)

init_db()

if __name__ == '__main__':
    app.run(debug=True)
