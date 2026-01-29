from flask import Flask, render_template, request, redirect, session
import sqlite3
import bcrypt

app = Flask(__name__)
app.secret_key = "secret123"


# ---------------------------
# DATABASE CONNECTION
# ---------------------------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------
# CREATE TABLES
# ---------------------------
def create_tables():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT,
            password BLOB
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS about_me(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            role TEXT,
            bio TEXT,
            skills TEXT,
            education TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS projects(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            project_name TEXT,
            description TEXT,
            github TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS contact(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            email TEXT,
            phone TEXT,
            linkedin TEXT,
            github TEXT
        )
    """)

    conn.commit()
    conn.close()


create_tables()


# ----------------------------------
# PASSWORD HASHING FUNCTION
# ----------------------------------
def hash_fun(plain_text):
    plain_text = plain_text.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_text, salt)
    return hashed


# ---------------------------
# WELCOME PAGE
# ---------------------------
@app.route('/')
def welcome():
    return render_template("welcome.html")


# ---------------------------
# LOGIN
# ---------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        email = request.form['email'].strip()
        password = request.form['password'].strip()

        if not email or not password:
            return render_template('login.html', result="Please fill in all fields")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cur.fetchone()

        if user:
            stored_hash = user['password']

            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode('utf-8')

            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect('/home')

        return render_template('login.html', result="Incorrect Email or Password")

    return render_template("login.html")


# ---------------------------
# SIGNUP
# ---------------------------
@app.route('/signup', methods=['GET', 'POST'])
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':

        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password'].strip()
        confirm = request.form['confirm_password'].strip()

        if not username or not email or not password or not confirm:
            return render_template("signup.html", result="Please fill in all fields")

        if len(password) < 6:
            return render_template("signup.html", result="Password must be at least 6 characters")

        if password != confirm:
            return render_template("signup.html", result="Passwords do not match")

        conn = get_db()
        cur = conn.cursor()

        # Check if email exists
        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        exist = cur.fetchone()

        if exist:
            return render_template("signup.html", result="Email already exists")

        # Hash password
        hashed_password = hash_fun(password)

        # Insert new user
        cur.execute(
            "INSERT INTO users(username, email, password) VALUES (?, ?, ?)",
            (username, email, hashed_password)
        )
        conn.commit()

        # Get the inserted user
        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        new_user = cur.fetchone()

        # Log in automatically
        session['user_id'] = new_user['id']
        session['username'] = new_user['username']

        return redirect('/home')

    return render_template("signup.html")

# ---------------------------
# HOME
# ---------------------------
@app.route('/home')
def home():
    if 'username' not in session:
        return redirect('/login')
    return render_template('home.html', username=session['username'])


# ---------------------------
# ABOUT ME
# ---------------------------
@app.route('/about', methods=['GET', 'POST'])
def about():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM about_me WHERE user_id=?", (user_id,))
    about_data = cur.fetchone()

    if request.method == 'POST':
        name = request.form['name'].strip()
        role = request.form['role'].strip()
        bio = request.form['bio'].strip()
        skills = request.form['skills'].strip()
        education = request.form['education'].strip()

        if not name or not role or not bio or not skills or not education:
            return render_template("about.html", about=about_data, result="All fields are required")

        cur.execute("DELETE FROM about_me WHERE user_id=?", (user_id,))
        cur.execute("""
            INSERT INTO about_me(user_id, name, role, bio, skills, education)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, name, role, bio, skills, education))
        conn.commit()

        return redirect('/about')

    return render_template("about.html", about=about_data)


# ---------------------------
# PROJECTS
# ---------------------------
@app.route('/projects', methods=['GET', 'POST'])
def projects():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM projects WHERE user_id=?", (user_id,))
    all_projects = cur.fetchall()

    if request.method == 'POST':
        project_name = request.form['project_name'].strip()
        description = request.form['description'].strip()
        github = request.form['github'].strip()

        if not project_name or not description or not github:
            return render_template("projects.html", projects=all_projects, result="All fields are required")

        cur.execute("""
            INSERT INTO projects(user_id, project_name, description, github)
            VALUES (?, ?, ?, ?)
        """, (user_id, project_name, description, github))
        conn.commit()

        return redirect('/projects')

    return render_template("projects.html", projects=all_projects)


# ---------------------------
# CONTACT
# ---------------------------
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM contact WHERE user_id=?", (user_id,))
    contact_data = cur.fetchone()

    if request.method == 'POST':
        email = request.form['email'].strip()
        phone = request.form['phone'].strip()
        linkedin = request.form['linkedin'].strip()
        github = request.form['github'].strip()

        if not email or not phone or not linkedin or not github:
            return render_template("contact.html", contact=contact_data, result="All fields are required")

        cur.execute("DELETE FROM contact WHERE user_id=?", (user_id,))
        cur.execute("""
            INSERT INTO contact(user_id, email, phone, linkedin, github)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, email, phone, linkedin, github))
        conn.commit()

        return redirect('/contact')

    return render_template("contact.html", contact=contact_data)


# ---------------------------
# PREVIEW PAGE
# ---------------------------
@app.route('/preview')
def preview():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM about_me WHERE user_id=?", (user_id,))
    about = cur.fetchone()

    cur.execute("SELECT * FROM projects WHERE user_id=?", (user_id,))
    projects = cur.fetchall()

    cur.execute("SELECT * FROM contact WHERE user_id=?", (user_id,))
    contact = cur.fetchone()

    return render_template("preview.html", about=about, projects=projects, contact=contact)


# ---------------------------
# LOGOUT
# ---------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ---------------------------
# EDIT PROJECT
# ---------------------------
@app.route('/edit_project/<int:id>', methods=['GET', 'POST'])
def edit_project(id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM projects WHERE id=?", (id,))
    project = cur.fetchone()

    if request.method == 'POST':
        name = request.form['project_name'].strip()
        description = request.form['description'].strip()
        github = request.form['github'].strip()

        if not name or not description or not github:
            return render_template("edit_project.html", project=project, result="All fields are required")

        cur.execute("""
            UPDATE projects
            SET project_name=?, description=?, github=?
            WHERE id=?
        """, (name, description, github, id))
        conn.commit()

        return redirect('/projects')

    return render_template("edit_project.html", project=project)


# ---------------------------
# DELETE PROJECT
# ---------------------------
@app.route('/delete_project/<int:id>')
def delete_project(id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM projects WHERE id=?", (id,))
    conn.commit()

    return redirect('/projects')



if __name__ == "__main__":
    app.run(debug=True)
