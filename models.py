from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(50))


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    deadline = db.Column(db.String(50))
    funds = db.Column(db.Float)
    contractor_id = db.Column(db.Integer)


class Labour(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    user_id = db.Column(db.Integer)


class LabourAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    labour_id = db.Column(db.Integer)
    project_id = db.Column(db.Integer)
    role = db.Column(db.String(100))
    daily_wage = db.Column(db.Float)
    total_wage = db.Column(db.Float, default=0)


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    labour_id = db.Column(db.Integer)
    project_id = db.Column(db.Integer)
    date = db.Column(db.String(50))
    status = db.Column(db.String(20))


class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer)
    name = db.Column(db.String(100))
    cost = db.Column(db.Float)