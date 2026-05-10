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

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY'
)

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

# ログイン画面

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

# ダッシュボード

@app.route('/dashboard')
@login_required
def dashboard():

    return render_template(
        'dashboard.html',
        user=current_user
    )

# 筋トレ

@app.route('/training')
@login_required
def training():

    return render_template(
        'training.html'
    )

# 支出管理

@app.route('/money')
@login_required
def money():

    return render_template(
        'money.html'
    )

# スケジュール

@app.route('/schedule')
@login_required
def schedule():

    return render_template(
        'schedule.html'
    )

# ログアウト

@app.route('/logout')
@login_required
def logout():

    logout_user()

    return redirect(
        url_for('index')
    )

if __name__ == '__main__':

    app.run(debug=True)