from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
import os
from config import Config
from models import db, User, Project, Labour, LabourAssignment, Material, Attendance

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

# ================= HELPERS ================= #

def is_logged_in():
    return 'user_id' in session

def require_role(role):
    return session.get('role') == role

# ================= AUTH ================= #

@app.route('/', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if not user:
            return "User not found"

        if not check_password_hash(user.password, password):
            return "Wrong password"

        session['user_id'] = user.id
        session['role'] = user.role

        return redirect('/dashboard')

    return render_template('login.html')


@app.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        # 🔒 Check duplicate
        if User.query.filter_by(username=username).first():
            return "Username already exists"

        # 🔒 Validate role
        if role not in ["Admin", "Contractor", "Labour"]:
            return "Invalid role"

        user = User(
            username=username,
            password=generate_password_hash(password),
            role=role
        )

        db.session.add(user)
        db.session.commit()

        # 🔥 Create labour profile if needed
        if role == "Labour":
            labour = Labour(
                name=username,
                user_id=user.id
            )
            db.session.add(labour)
            db.session.commit()

        return redirect('/')

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ================= DASHBOARD ================= #

@app.route('/dashboard')
def dashboard():

    if not is_logged_in():
        return redirect('/')

    role = session.get('role')
    user_id = session.get('user_id')

    # ================= ADMIN ================= #
    if role == "Admin":

        return render_template(
            'dashboard.html',
            role=role,
            projects=Project.query.all(),
            assignments=LabourAssignment.query.all(),
            materials=Material.query.all(),
            contractors=User.query.filter_by(role='Contractor').all()
        )

    # ================= CONTRACTOR ================= #
    elif role == "Contractor":

        projects = Project.query.filter_by(contractor_id=user_id).all()

        return render_template(
            'dashboard.html',
            role=role,
            projects=projects,
            labours=Labour.query.all(),
            assignments=LabourAssignment.query.all(),
            materials=Material.query.all()
        )

    # ================= LABOUR ================= #
    elif role == "Labour":

        labour = Labour.query.filter_by(user_id=user_id).first()

        return render_template(
            'dashboard.html',
            role=role,
            assignments=LabourAssignment.query.filter_by(labour_id=labour.id).all(),
            attendance=Attendance.query.filter_by(labour_id=labour.id).all()
        )

# ================= ADMIN ROUTES ================= #

@app.route('/create_project', methods=['POST'])
def create_project():

    if not require_role("Admin"):
        return "Access Denied"

    project = Project(
        name=request.form['name'],
        deadline=request.form['deadline'],
        funds=float(request.form['funds']),
        contractor_id=int(request.form['contractor_id'])
    )

    db.session.add(project)
    db.session.commit()

    return redirect('/dashboard')

# ================= CONTRACTOR ROUTES ================= #

@app.route('/create_labour', methods=['POST'])
def create_labour():

    if not require_role("Contractor"):
        return "Access Denied"

    labour = Labour(name=request.form['name'])

    db.session.add(labour)
    db.session.commit()

    return redirect('/dashboard')


@app.route('/assign_labour', methods=['POST'])
def assign_labour():

    if not require_role("Contractor"):
        return "Access Denied"

    user_id = session['user_id']
    project_id = int(request.form['project_id'])

    # 🔐 SECURITY CHECK
    project = Project.query.filter_by(id=project_id, contractor_id=user_id).first()
    if not project:
        return "Unauthorized Project Access"

    assignment = LabourAssignment(
        labour_id=int(request.form['labour_id']),
        project_id=project_id,
        role=request.form['role'],
        daily_wage=float(request.form['daily_wage'])
    )

    db.session.add(assignment)
    db.session.commit()

    return redirect('/dashboard')


@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():

    if not require_role("Contractor"):
        return "Access Denied"

    labour_id = int(request.form['labour_id'])
    project_id = int(request.form['project_id'])
    status = request.form['status']

    today = str(date.today())

    attendance = Attendance(
        labour_id=labour_id,
        project_id=project_id,
        date=today,
        status=status
    )

    db.session.add(attendance)

    # 🔥 Wage Auto Update
    if status == "Present":

        assignment = LabourAssignment.query.filter_by(
            labour_id=labour_id,
            project_id=project_id
        ).first()

        if assignment:
            assignment.total_wage += assignment.daily_wage

    db.session.commit()

    return redirect('/dashboard')


@app.route('/add_material', methods=['POST'])
def add_material():

    if not require_role("Contractor"):
        return "Access Denied"

    user_id = session['user_id']
    project_id = int(request.form['project_id'])

    # 🔐 SECURITY CHECK
    project = Project.query.filter_by(id=project_id, contractor_id=user_id).first()
    if not project:
        return "Unauthorized Project"

    material = Material(
        project_id=project_id,
        name=request.form['name'],
        cost=float(request.form['cost'])
    )

    db.session.add(material)
    db.session.commit()

    return redirect('/dashboard')

# ================= RUN ================= #

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)