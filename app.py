from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import random
from datetime import datetime


def generate_unique_quiz_link():
    # Generate a secure, random token
    return secrets.token_urlsafe(10)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

REGISTRATION_KEY = "YourSecretKeyHere"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='admin')  # Default role

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(200), nullable=False)
    # Assuming options and correct answer fields are handled within or related to this model
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)  # Link to the Quiz model

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    time_limit = db.Column(db.Integer, nullable=True)  # Notice the field name is time_limit
    link = db.Column(db.String(255), unique=True, nullable=False)
    num_questions_display = db.Column(db.Integer, nullable=False, default=10)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    questions = db.relationship('Question', backref='quiz', lazy='dynamic')


@app.before_first_request
def create_tables():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('admin_dashboard')) if user.role == 'admin' else redirect(url_for('user_dashboard'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        registration_key = request.form['registration_key']
        
        if registration_key != REGISTRATION_KEY:
            flash('Invalid registration key')
            return render_template('register.html')
        
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Username already exists')
            return render_template('register.html')

        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for('admin_dashboard'))
    return render_template('register.html')

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return 'Access Denied', 403
    return render_template('admin_dashboard.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/add_quiz', methods=['GET', 'POST'])
@login_required
def add_quiz():
    if request.method == 'POST':
        quiz_title = request.form.get('quiz_title')
        quiz_time = request.form.get('quiz_time')
        num_questions_display = int(request.form.get('num_questions_display'))
        
        # Assuming you have a function to generate a unique quiz link
        quiz_link = generate_unique_quiz_link()

        # Create the quiz with the provided details
        new_quiz = Quiz(title=quiz_title, time_limit=quiz_time, link=quiz_link, admin_id=current_user.id)
        db.session.add(new_quiz)
        db.session.flush()  # To get the new_quiz.id for further use before committing
        
        # Here you should also process the added questions and options
        # For simplicity, this step is not shown. You would parse the questions and options
        # from the form, create Question and Option objects, and link them to the new_quiz.
        
        db.session.commit()
        
        # Optionally, redirect to a page showing the quiz details, including the link
        return redirect(url_for('quiz_details', quiz_id=new_quiz.id))
    return render_template('add_quiz.html')

@app.route('/view_results')
@login_required
def view_results():
    # Fetch quiz results from the database
    results = []  # Replace this with your actual logic to fetch results
    return render_template('view_results.html', results=results)  # You need to create this template

@app.route('/quiz/<quiz_link>')
def take_quiz(quiz_link):
    quiz = Quiz.query.filter_by(link=quiz_link).first_or_404()
    
    # Fetch all questions for the quiz
    questions = quiz.questions  # Assuming a relationship is set up in your models
    
    # Randomly select the specified number of questions
    displayed_questions = random.sample(questions, min(len(questions), quiz.num_questions_display))
    
    # Render a template to display these questions
    return render_template('take_quiz.html', questions=displayed_questions, quiz=quiz)

if __name__ == '__main__':
    app.run(debug=True)
