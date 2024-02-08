# app/routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
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

        if registration_key != main.config['ADMIN_REGISTRATION_KEY']:
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
        return redirect(url_for('main.admin_login'))  # Redirect specifically to the admin login page
    else:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.login'))  # Fallback for non-admins trying to access the admin logout

@main.route('/add_quiz', methods=['GET', 'POST'])
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
        return redirect(url_for('main.quiz_details', quiz_id=new_quiz.id))
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
