from . import db
from flask_login import UserMixin
from datetime import datetime
import secrets
import uuid

def generate_random_link_uuid():
    return str(uuid.uuid4())

def generate_random_link_secrets():
    return secrets.token_urlsafe(8)  # Adjust the length as needed

def generate_unique_quiz_link():
    while True:
        random_link = generate_random_link_secrets()  # or generate_random_link_uuid()
        existing_quiz = Quiz.query.filter_by(link=random_link).first()
        if not existing_quiz:
            return random_link

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    usn = db.Column(db.String(10), unique=True, nullable=True)  # Allow null for admins
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='user')
    results = db.relationship('Result', backref='user', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    correct_answer = db.Column(db.String(200), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    options = db.relationship('Option', backref='question', lazy=True, cascade="all, delete-orphan")
    points = db.Column(db.Integer, nullable=False, default=1)

class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    time_limit = db.Column(db.Integer, nullable=True)  # Time limit in minutes
    num_questions_display = db.Column(db.Integer, nullable=False)
    link = db.Column(db.String(255), unique=True, nullable=False, default=generate_unique_quiz_link)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    questions = db.relationship('Question', backref='quiz', lazy=True, cascade='all, delete-orphan')
    results = db.relationship('Result', backref='quiz', lazy=True)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
