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

# Flask作成

app = Flask(__name__)

# SECRET_KEY

app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY'
)

# Render環境変数

USERNAME = os.environ.get(
    'APP_USERNAME'
)

PASSWORD = os.environ.get(
    'APP_PASSWORD'
)

# 固定ログイン情報

USER_DATA = {
    USERNAME: generate_password_hash(PASSWORD)
}

# LoginManager

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = 'login'

# Userクラス

class User(UserMixin):

    def __init__(self, username):

        self.id = username

# ユーザー読み込み

@login_manager.user_loader
def load_user(user_id):

    return User(user_id)

# トップページ

@app.route('/')
def index():

    return render_template('index.html')

# ログイン

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']

        password = request.form['password']

        # ユーザー存在確認

        if username in USER_DATA:

            hashed_password = USER_DATA[username]

            # パスワード確認

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

    return render_template('login.html')

# ダッシュボード

@app.route('/dashboard')
@login_required
def dashboard():

    return render_template(
        'dashboard.html',
        user=current_user
    )

# ログアウト

@app.route('/logout')
@login_required
def logout():

    logout_user()

    return redirect(
        url_for('index')
    )

# 起動

if __name__ == '__main__':

    app.run(debug=True)