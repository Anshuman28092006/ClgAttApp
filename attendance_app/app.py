from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import qrcode
from io import BytesIO
import base64
import datetime
import uuid  # For unique session IDs

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # Change this for production

# Database setup
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY, student_id INTEGER, class_id TEXT, date TEXT, status TEXT)''')
    # Add demo users: faculty (username: faculty1, pw: pass), student (username: student1, pw: pass)
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('faculty1', 'pass', 'faculty')")
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('student1', 'pass', 'student')")
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            session['role'] = user[3]
            if session['role'] == 'faculty':
                return redirect(url_for('faculty_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/faculty_dashboard')
def faculty_dashboard():
    if 'role' not in session or session['role'] != 'faculty':
        return redirect(url_for('login'))
    # Fake attendance data for demo
    attendance_data = [
        {'student': 'Student1', 'date': '2025-08-29', 'status': 'Present'},
        {'student': 'Student2', 'date': '2025-08-29', 'status': 'Absent'}
    ]
    return render_template('faculty_dashboard.html', attendance_data=attendance_data)

@app.route('/generate_qr', methods=['GET', 'POST'])
def generate_qr():
    if 'role' not in session or session['role'] != 'faculty':
        return redirect(url_for('login'))
    qr_data = None
    class_id = str(uuid.uuid4())  # Unique class session ID
    if request.method == 'POST':
        # Generate dynamic QR with class_id and timestamp (valid for 3 mins)
        timestamp = datetime.datetime.now().isoformat()
        qr_content = f"attendance:{class_id}:{timestamp}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_content)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        qr_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
        flash('QR generated! Students can scan now.')
    return render_template('generate_qr.html', qr_data=qr_data, class_id=class_id)

@app.route('/student_dashboard')
def student_dashboard():
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    # Fake calendar data for demo (attendance tracker)
    calendar_data = [
        {'date': '2025-08-28', 'status': 'Present'},
        {'date': '2025-08-29', 'status': 'Absent'}
    ]
    attendance_percentage = 50  # Fake calc
    return render_template('student_dashboard.html', calendar_data=calendar_data, percentage=attendance_percentage)

@app.route('/scan_qr', methods=['GET', 'POST'])
def scan_qr():
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    if request.method == 'POST':
        scanned_qr = request.form['scanned_qr']  # In real, this would come from JS scanner; here simulate
        # Validate QR (simple check for demo)
        if 'attendance:' in scanned_qr:
            # Simulate geofencing: In real, check lat/long from JS
            # For now, assume valid if within time
            parts = scanned_qr.split(':')
            timestamp = datetime.datetime.fromisoformat(parts[2])
            if (datetime.datetime.now() - timestamp).total_seconds() < 180:  # 3 mins
                conn = sqlite3.connect('database.db')
                c = conn.cursor()
                c.execute("INSERT INTO attendance (student_id, class_id, date, status) VALUES (?, ?, ?, ?)",
                          (session['user_id'], parts[1], datetime.date.today(), 'Present'))
                conn.commit()
                conn.close()
                flash('Attendance marked! Geofence validated.')
            else:
                flash('QR expired or invalid geofence.')
        else:
            flash('Invalid QR.')
    return render_template('scan_qr.html')

if __name__ == '__main__':
    app.run(debug=True)
