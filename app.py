import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)

from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY'
)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    'sqlite:///training.db'
)

db = SQLAlchemy(app)

USERNAME = os.environ.get(
    'APP_USERNAME'
)

PASSWORD = os.environ.get(
    'APP_PASSWORD'
)

USER_DATA = {
    USERNAME: generate_password_hash(PASSWORD)
}

login_manager = LoginManager()

login_manager.init_app(app)

class User(UserMixin):

    def __init__(self, username):

        self.id = username

@login_manager.user_loader
def load_user(user_id):

    return User(user_id)

# =========================
# Workout Model
# =========================

class Workout(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    exercise = db.Column(
        db.String(100)
    )

    weight = db.Column(
        db.String(50)
    )

    reps = db.Column(
        db.String(50)
    )

    sets = db.Column(
        db.String(50)
    )

# =========================
# Login
# =========================

@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'POST':

        username = request.form['username']

        password = request.form['password']

        if username in USER_DATA:

            hashed_password = USER_DATA[username]

            if check_password_hash(
                hashed_password,
                password
            ):

                user = User(username)

                login_user(user)

                return redirect(
                    url_for('dashboard')
                )

        flash('ログイン失敗')

    return render_template('index.html')

# =========================
# Dashboard
# =========================

@app.route('/dashboard')
@login_required
def dashboard():

    return render_template(
        'dashboard.html',
        user=current_user
    )

# =========================
# Training
# =========================

@app.route('/training')
@login_required
def training():

    workouts = Workout.query.order_by(
        Workout.id.desc()
    ).all()

    return render_template(
        'training.html',
        workouts=workouts
    )

# =========================
# Add Workout
# =========================

@app.route('/add_workout', methods=['POST'])
@login_required
def add_workout():

    exercise = request.form['exercise']

    weight = request.form['weight']

    reps = request.form['reps']

    sets = request.form['sets']

    workout = Workout(
        exercise=exercise,
        weight=weight,
        reps=reps,
        sets=sets
    )

    db.session.add(workout)

    db.session.commit()

    return redirect(
        url_for('training')
    )

# =========================
# Delete Workout
# =========================

@app.route('/delete_workout/<int:id>')
@login_required
def delete_workout(id):

    workout = Workout.query.get(id)

    db.session.delete(workout)

    db.session.commit()

    return redirect(
        url_for('training')
    )

# =========================
# Money
# =========================

@app.route('/money')
@login_required
def money():

    return render_template(
        'money.html'
    )

# =========================
# Schedule
# =========================

@app.route('/schedule')
@login_required
def schedule():

    return render_template(
        'schedule.html'
    )

# =========================
# Logout
# =========================

@app.route('/logout')
@login_required
def logout():

    logout_user()

    return redirect(
        url_for('index')
    )

# =========================
# Run
# =========================

if __name__ == '__main__':

    with app.app_context():

        db.create_all()

    app.run(debug=True)