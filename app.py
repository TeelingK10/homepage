from flask import Flask, render_template, request, redirect, url_for, flash

from flask_sqlalchemy import SQLAlchemy

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

# Flask初期化

app = Flask(__name__)

# 設定

app.config['SECRET_KEY'] = 'secret-key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

# DB初期化

db = SQLAlchemy(app)

# LoginManager初期化

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = 'login'

# Userモデル

class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(200),
        nullable=False
    )

# ユーザー読み込み

@login_manager.user_loader
def load_user(user_id):

    return User.query.get(int(user_id))

# トップページ

@app.route('/')
def index():

    return render_template('index.html')

# 新規登録

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']

        password = request.form['password']

        # 同じユーザー確認

        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:

            flash('このユーザーは既に存在します')

            return redirect(url_for('register'))

        # パスワード暗号化

        hashed_password = generate_password_hash(password)

        # ユーザー作成

        new_user = User(
            username=username,
            password=hashed_password
        )

        db.session.add(new_user)

        db.session.commit()

        flash('登録成功')

        return redirect(url_for('login'))

    return render_template('register.html')

# ログイン

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']

        password = request.form['password']

        user = User.query.filter_by(
            username=username
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            login_user(user)

            return redirect(url_for('dashboard'))

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

    return redirect(url_for('index'))

# 実行

if __name__ == '__main__':

    with app.app_context():

        db.create_all()

    app.run(debug=True)