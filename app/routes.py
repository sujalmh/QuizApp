from flask import Blueprint, current_app, render_template, redirect, url_for, flash, request, abort, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Quiz, Question, Option, Result, UserAnswer, QuizAttempt
from . import db, login_manager
import random
import re
from datetime import datetime, timedelta
import uuid
import secrets
import pytz


main = Blueprint('main', __name__)
ist_timezone = pytz.timezone('Asia/Kolkata')


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

def get_random_questions(quiz_id, num_questions):
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    return random.sample(questions, num_questions) if len(questions) >= num_questions else questions

@login_manager.user_loader
def load_user(user_id):
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
            session['user_id'] = user.id
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
        return redirect(url_for('main.login')) 
    quizzes = Quiz.query.filter_by(admin_id=current_user.id).all()
    return render_template('admin_dashboard.html', quizzes=quizzes)

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

@main.route('/add_quiz', methods=['GET', 'POST'])
@login_required
def add_quiz():
    if request.method == 'POST':
        title = request.form.get('quiz_title')
        time_limit = request.form.get('quiz_time', type=int)
        num_questions_display = request.form.get('num_questions_display', type=int)
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        start_time_naive  = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
        end_time_naive = datetime.strptime(end_time, '%Y-%m-%dT%H:%M')
        start_time = ist_timezone.localize(start_time_naive)
        end_time = ist_timezone.localize(end_time_naive)

        new_quiz = Quiz(
            title=title,
            time_limit=time_limit,
            num_questions_display=num_questions_display,
            admin_id=current_user.id,
            link=generate_unique_quiz_link(),
            start_time=start_time,
            end_time=end_time
        )
        
        db.session.add(new_quiz)
        db.session.commit()

        for key, value in request.form.items():
            if 'questions[' in key and 'text' in key:

                start = key.find('[') + 1
                end = key.find(']')
                question_index = int(key[start:end])

                question_text = value
                question_points = request.form.get(f'questions[{question_index}][points]', type=int)
                
                question = Question(
                    text=question_text,
                    points=question_points,
                    correct_answer="",  
                    quiz_id=new_quiz.id
                )
                db.session.add(question)
                db.session.commit()  

                options_count = len([k for k in request.form if f'questions[{question_index}][options]' in k])
                correct_answer_index = int(request.form.get(f'questions[{question_index}][correct_answer]'))

                for option_index in range(options_count):
                    option_text = request.form.get(f'questions[{question_index}][options][{option_index}]')
                    option = Option(text=option_text, question_id=question.id)
                    db.session.add(option)
                    
                    if option_index == correct_answer_index:
                        print(option.id, type(option.id))
                        question.correct_answer = option_text
                db.session.commit()

        flash('Quiz added successfully!')
        return redirect(url_for('main.admin_dashboard'))
    return render_template('add_quiz.html')

@main.route('/attempted/<quiz_link>')
@login_required
def attempted(quiz_link):
    quiz = Quiz.query.filter_by(link=quiz_link).first_or_404()
    return render_template('attempted.html', quiz_link=quiz_link)

@main.route('/quiz/<quiz_link>')
@login_required
def take_quiz(quiz_link):
    quiz = Quiz.query.filter_by(link=quiz_link).first_or_404()

    now_ist = datetime.now(ist_timezone)
    
    if now_ist < quiz.start_time.astimezone(ist_timezone):
        flash('This quiz has not started yet.', 'warning')
        return redirect(url_for('main.dashboard'))
    elif now_ist > quiz.end_time.astimezone(ist_timezone):
        flash('This quiz has already ended.', 'warning')
        return redirect(url_for('main.dashboard'))

    existing_result = Result.query.filter_by(user_id=current_user.id, quiz_id=quiz.id).first()
    if existing_result:
        flash('You have already attempted this quiz.', 'error')
        return redirect(url_for('main.attempted',quiz_link=quiz_link))
    
    attempt = QuizAttempt.query.filter_by(user_id=current_user.id, quiz_id=quiz.id, completed=False).first()
    
    if not attempt:
        all_questions = Question.query.filter_by(quiz_id=quiz.id).all()
        selected_questions = random.sample(all_questions, min(len(all_questions), quiz.num_questions_display))
        attempt = QuizAttempt(user_id=current_user.id, quiz_id=quiz.id, timestamp=now_ist + timedelta(minutes=quiz.time_limit))
        db.session.add(attempt)
        attempt.questions.extend(selected_questions)
        db.session.commit()
    else:
        selected_questions = attempt.questions
        
    return render_template('take_quiz.html', quiz=quiz, questions=selected_questions, attempt_id=attempt.id, end_time=attempt.timestamp)

@main.route('/admin/view_quiz/<quiz_link>')
def admin_view_quiz(quiz_link):
    quiz = Quiz.query.filter_by(link=quiz_link).first_or_404()
    questions = Question.query.filter_by(quiz_id=quiz.id).all()
    return render_template('view_quiz.html', quiz=quiz, questions=questions)

@main.route('/admin/delete_quiz/<quiz_link>', methods=['POST'])
def delete_quiz(quiz_link):
    quiz = Quiz.query.filter_by(link=quiz_link).first_or_404()
    Question.query.filter_by(quiz_id=quiz.id).delete()  # Delete related questions
    db.session.delete(quiz)
    db.session.commit()
    flash('Quiz and related questions deleted successfully.', 'success')
    return redirect(url_for('main.admin_dashboard'))

@main.route('/submit_quiz/<quiz_link>', methods=['POST'])
@login_required
def submit_quiz(quiz_link):
    attempt_id = request.form.get('attempt_id')
    attempt = QuizAttempt.query.filter_by(id=attempt_id, user_id=current_user.id).first_or_404()

    score = 0
    for question in attempt.quiz.questions:
        selected_option_text = request.form.get(f'question_{question.id}')

        if selected_option_text:  # Check if an option was selected
            # Find the option in the question's options based on the text
            selected_option = next((option for option in question.options if option.text == selected_option_text), None)

            if selected_option:
                # Create a UserAnswer record with the selected option's ID
                user_answer = UserAnswer(
                    user_id=current_user.id,
                    quiz_id=attempt.quiz_id,
                    question_id=question.id,
                    option_id=selected_option.id,  # Use the ID of the found option
                    attempt_id=attempt.id
                )
                db.session.add(user_answer)

                # Check if the selected option's text matches the correct answer text
                if selected_option_text == question.correct_answer:
                    score += question.points
            else:
                # Handle the case where no matching option is found; might indicate an issue or unexpected data
                pass
        else:
            # Optionally handle the case where no option was selected for a question
            pass
    result = Result(score=score, user_id=current_user.id, quiz_id=attempt.quiz.id, attempted=True, timestamp=datetime.utcnow())
    db.session.add(result)
        
    attempt.completed = True  # Mark the attempt as completed
    db.session.commit()

    flash(f'Quiz submitted successfully! Your score: {score}', 'success')
    return redirect(url_for('main.quiz_results', quiz_link=quiz_link))

@main.route('/results')
def results():
    if not session.get('user_id'):  # Assuming you're using Flask's session to track logged in users
        flash('You must be logged in to submit quizzes.', 'danger')
        return redirect(url_for('main.login'))
    
    user_id = session['user_id']
    user_results = Result.query.filter_by(user_id=user_id).all()
    return render_template('results.html', user_results=user_results)

@main.route('/quiz_results/<quiz_link>')
@login_required
def quiz_results(quiz_link):
    quiz = Quiz.query.filter_by(link=quiz_link).first_or_404()
    attempt = QuizAttempt.query.filter_by(user_id=current_user.id, quiz_id=quiz.id, completed=True).first_or_404()
    result = Result.query.filter_by(user_id=current_user.id, quiz_id=quiz.id).first_or_404()
    # Fetch user answers for detailed results, if necessary
    user_answers = UserAnswer.query.filter_by(user_id=current_user.id, quiz_id=quiz.id).all()

    score = result.score  # Placeholder, replace with actual logic to fetch the score

    return render_template('quiz_results.html', quiz=quiz, score=score, attempt=attempt, result=result, user_answers=user_answers)

@main.route('/admin/quiz_results/<quiz_link>')
@login_required
def admin_quiz_results(quiz_link):
    # Ensure the current user is an admin
    if not current_user.role == 'admin':
        flash('Access denied: Requires admin privileges.', 'error')
        return redirect(url_for('main.dashboard'))

    quiz = Quiz.query.filter_by(link=quiz_link).first_or_404()

    attempts = QuizAttempt.query.filter_by(quiz_id=quiz.id).all()

    results = Result.query.filter_by(quiz_id=quiz.id).all()
    attempts_results = [{'attempt': attempt, 'result': result} for attempt, result in zip(attempts, results)]

    return render_template('admin_quiz_results.html', quiz=quiz, attempts_results=attempts_results)

@main.route('/<path:path>', methods=['GET', 'POST'])
def catch_all(path):
    print(f"Unhandled path: {path}")
    return f"Path requested: {path}", 404

@main.route('/admin/quiz_attempt_details/<quiz_link>/<int:attempt_id>')
@login_required
def quiz_attempt_details(quiz_link, attempt_id):
    if not current_user.role == 'admin':
        flash('Access denied: Requires admin privileges.', 'error')
        return redirect(url_for('main.dashboard'))
    
    quiz = Quiz.query.filter_by(link=quiz_link).first_or_404()
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    user_answers = UserAnswer.query.filter_by(attempt_id=attempt.id).all()
    result = Result.query.filter_by(user_id=attempt.user_id, quiz_id=attempt.quiz_id).first()
    return render_template('quiz_attempt_details.html', quiz=quiz, attempt=attempt, user_answers=user_answers, result=result)

@main.route('/enter_quiz', methods=['POST'])
@login_required
def enter_quiz():
    quiz_code = request.form.get('quiz_code')
    quiz = Quiz.query.filter_by(link=quiz_code).first()
    
    if quiz:
        return redirect(url_for('main.take_quiz', quiz_link=quiz_code))
    else:
        flash('Quiz code is invalid.', 'error')
        return redirect(url_for('main.dashboard'))
