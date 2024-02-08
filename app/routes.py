# app/routes.py

from flask import Blueprint, current_app, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Quiz, Question, Option, Result
from . import db, login_manager
import secrets
import random
import re

main = Blueprint('main', __name__)
def generate_unique_quiz_link():
    return secrets.token_urlsafe(10)

@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))

@main.route('/')
def home():
    return render_template('index.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('main.admin_dashboard'))  # Redirect admin to admin dashboard
            else:
                return redirect(url_for('main.dashboard'))  # Redirect regular user to dashboard
        else:
            flash('Invalid username or password.')
    
    return render_template('login.html')  # Render the login template

@main.route('/admin/register', methods=['GET', 'POST'])
def admin_register():

    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        registration_key = request.form.get('registration_key')

        if registration_key != current_app.config['ADMIN_REGISTRATION_KEY']:
            flash('Invalid registration key.')
            return redirect(url_for('main.admin_register'))

        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Username already exists.')
            return redirect(url_for('main.admin_register'))

        hashed_password = generate_password_hash(password)
        new_admin = User(name=name, username=username, password=hashed_password, role='admin', usn=None)  # Explicitly set usn to None for admins
        db.session.add(new_admin)
        db.session.commit()
        login_user(new_admin)

        flash('New admin created successfully.')
        return redirect(url_for('main.admin_dashboard'))

    return render_template('admin_register.html')


@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        usn = request.form.get('usn').upper()  # Ensure USN is uppercase
        username = request.form['username']
        password = request.form['password']
        
        # Validate USN format
        if not re.match(r"4MT\d\d[A-Z][A-Z]\d\d\d", usn):
            flash('USN must be in the format 4MT**$$***.')
            return render_template('register.html')
        
        # Check if the USN already exists
        user_exists = User.query.filter_by(usn=usn).first()
        if user_exists:
            flash('USN already exists')
            return render_template('register.html')
        username_exists = User.query.filter_by(username=username).first()
        if username_exists:
            flash('Username already exists')
            return render_template('register.html')
        hashed_password = generate_password_hash(password)
        new_user = User(name=name, usn=usn, username=username, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful!')
            return redirect(url_for('main.login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Error: {}'.format(str(e)))

        flash('Registration successful!')
        return redirect(url_for('main.login'))

    return render_template('register.html')

@main.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied: Admins only.', 'error')
        return redirect(url_for('main.login'))  # Redirect to a general user login page or homepage
    return render_template('admin_dashboard.html')

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/admin/logout')
@login_required
def admin_logout():
    if current_user.role == 'admin':
        logout_user()
        flash('You have been logged out.', 'success')
        return redirect(url_for('main.admin_logout'))  # Redirect specifically to the admin login page
    else:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.login'))  # Fallback for non-admins trying to access the admin logout

@main.route('/add_quiz', methods=['GET','POST'])
def add_quiz():
    if request.method == 'POST':
        title = request.form.get('quiz_title')
        time_limit = request.form.get('quiz_time')
        num_questions_display = request.form.get('num_questions_display')

        # Convert num_questions_display to int
        try:
            num_questions_display = int(num_questions_display)
        except (TypeError, ValueError):
            flash('Number of Questions to Display must be a valid number.')
            return redirect(url_for('some_route'))  # Adjust as needed

        link = generate_unique_quiz_link()
        admin_id = current_user.id  # Assuming current_user is set and has an id

        new_quiz = Quiz(title=title, time_limit=time_limit, num_questions_display=num_questions_display, link=link, admin_id=admin_id)
        
        try:
            db.session.add(new_quiz)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash('Error adding quiz: {}'.format(str(e)))
            return redirect(url_for('some_route'))  # Adjust as needed

        flash('Quiz added successfully!')
        return redirect(url_for('main.admin_dashboard'))  # Adjust as needed
    return render_template('add_quiz.html')

@main.route('/view_results')
@login_required
def view_results():
    # Fetch quiz results from the database
    results = []  # Replace this with your actual logic to fetch results
    return render_template('view_results.html', results=results)  # You need to create this template

@main.route('/quiz/<quiz_link>')
def take_quiz(quiz_link):
    quiz = Quiz.query.filter_by(link=quiz_link).first_or_404()
    
    # Fetch all questions for the quiz
    questions = quiz.questions  # Assuming a relationship is set up in your models
    
    # Randomly select the specified number of questions
    displayed_questions = random.sample(questions, min(len(questions), quiz.num_questions_display))
    
    # Render a template to display these questions
    return render_template('take_quiz.html', questions=displayed_questions, quiz=quiz)
