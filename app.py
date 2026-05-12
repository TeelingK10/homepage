import os
from datetime import datetime

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

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///training.db'

db = SQLAlchemy(app)

USERNAME = os.environ.get('APP_USERNAME', 'admin')
PASSWORD = os.environ.get('APP_PASSWORD', 'password')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'


class User(UserMixin):
    def __init__(self, username):
        self.id = username


@login_manager.user_loader
def load_user(user_id):
    if user_id == USERNAME:
        return User(user_id)
    return None


# =========================
# Models
# =========================

class Workout(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    exercise = db.Column(db.String(100))
    weight   = db.Column(db.Float)
    reps     = db.Column(db.Integer)
    sets     = db.Column(db.Integer)
    date     = db.Column(db.String(20))


class Menu(db.Model):
    """曜日ごとのトレーニングメニュー (day: 0=月〜6=日)"""
    id           = db.Column(db.Integer, primary_key=True)
    day          = db.Column(db.Integer)
    order        = db.Column(db.Integer)
    exercise     = db.Column(db.String(100))
    target_sets  = db.Column(db.Integer)
    target_reps  = db.Column(db.Integer)


class Expense(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    category    = db.Column(db.String(100))
    description = db.Column(db.String(200))
    amount      = db.Column(db.Integer)
    date        = db.Column(db.String(20))


class Event(db.Model):
    id    = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    date  = db.Column(db.String(20))
    time  = db.Column(db.String(10))
    note  = db.Column(db.String(300))


# =========================
# Helpers
# =========================

DAY_NAMES    = ['月', '火', '水', '木', '金', '土', '日']
DAY_NAMES_EN = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def get_pr_map():
    """種目名 → 最高重量(float)"""
    pr = {}
    for w in Workout.query.all():
        if w.weight is not None:
            if w.exercise not in pr or w.weight > pr[w.exercise]:
                pr[w.exercise] = w.weight
    return pr


def get_today_menu():
    today = datetime.now().weekday()  # 月=0, 日=6
    items = (
        Menu.query
        .filter_by(day=today)
        .order_by(Menu.order)
        .all()
    )
    return items, today


# =========================
# Login
# =========================

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == USERNAME and password == PASSWORD:
            login_user(User(username))
            return redirect(url_for('dashboard'))
        flash('ログイン失敗')
    return render_template('index.html')


# =========================
# Dashboard
# =========================

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)


# =========================
# Training
# =========================

@app.route('/training')
@login_required
def training():
    workouts      = Workout.query.order_by(Workout.id.desc()).all()
    pr_map        = get_pr_map()
    today_menu, today_day = get_today_menu()
    menus_by_day  = [
        Menu.query.filter_by(day=d).order_by(Menu.order).all()
        for d in range(7)
    ]
    return render_template(
        'training.html',
        workouts=workouts,
        pr_map=pr_map,
        today_menu=today_menu,
        today_day=today_day,
        day_names=DAY_NAMES,
        day_names_en=DAY_NAMES_EN,
        menus_by_day=menus_by_day,
        now=datetime.now().strftime('%Y-%m-%d')
    )


@app.route('/add_workout', methods=['POST'])
@login_required
def add_workout():
    db.session.add(Workout(
        exercise=request.form['exercise'],
        weight=float(request.form['weight']),
        reps=int(request.form['reps']),
        sets=int(request.form['sets']),
        date=request.form.get('date', datetime.now().strftime('%Y-%m-%d'))
    ))
    db.session.commit()
    return redirect(url_for('training'))


@app.route('/delete_workout/<int:id>')
@login_required
def delete_workout(id):
    w = db.session.get(Workout, id)
    if w:
        db.session.delete(w)
        db.session.commit()
    return redirect(url_for('training'))


# =========================
# Menu
# =========================

@app.route('/add_menu', methods=['POST'])
@login_required
def add_menu():
    day = int(request.form['day'])
    max_order = (
        db.session.query(db.func.max(Menu.order))
        .filter_by(day=day).scalar() or 0
    )
    db.session.add(Menu(
        day=day,
        order=max_order + 1,
        exercise=request.form['exercise'],
        target_sets=int(request.form['target_sets']),
        target_reps=int(request.form['target_reps'])
    ))
    db.session.commit()
    return redirect(url_for('training') + '#menu-section')


@app.route('/delete_menu/<int:id>')
@login_required
def delete_menu(id):
    m = db.session.get(Menu, id)
    if m:
        db.session.delete(m)
        db.session.commit()
    return redirect(url_for('training') + '#menu-section')


# =========================
# Money
# =========================

@app.route('/money')
@login_required
def money():
    # クエリパラメータで表示月を切り替え (例: ?month=2025-04)
    selected_month = request.args.get('month', datetime.now().strftime('%Y-%m'))

    # 全支出（降順）
    expenses = Expense.query.order_by(Expense.id.desc()).all()

    # 選択月のみ絞り込み
    month_expenses = [e for e in expenses if e.date.startswith(selected_month)]
    month_total    = sum(e.amount for e in month_expenses)

    # カテゴリ別集計（円グラフ用）
    category_totals = {}
    for e in month_expenses:
        category_totals[e.category] = category_totals.get(e.category, 0) + e.amount

    # 月一覧（セレクタ用）
    months = sorted({e.date[:7] for e in expenses}, reverse=True)
    if selected_month not in months:
        months.insert(0, selected_month)

    total = sum(e.amount for e in expenses)

    return render_template(
        'money.html',
        expenses=month_expenses,
        total=total,
        month_total=month_total,
        selected_month=selected_month,
        months=months,
        category_totals=category_totals,
    )


@app.route('/add_expense', methods=['POST'])
@login_required
def add_expense():
    db.session.add(Expense(
        category=request.form['category'],
        description=request.form['description'],
        amount=int(request.form['amount']),
        date=request.form['date']
    ))
    db.session.commit()
    return redirect(url_for('money'))


@app.route('/delete_expense/<int:id>')
@login_required
def delete_expense(id):
    e = db.session.get(Expense, id)
    if e:
        db.session.delete(e)
        db.session.commit()
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    return redirect(url_for('money', month=month))


# =========================
# Schedule
# =========================

@app.route('/schedule')
@login_required
def schedule():
    events = Event.query.order_by(Event.date, Event.time).all()
    return render_template('schedule.html', events=events)


@app.route('/add_event', methods=['POST'])
@login_required
def add_event():
    db.session.add(Event(
        title=request.form['title'],
        date=request.form['date'],
        time=request.form['time'],
        note=request.form.get('note', '')
    ))
    db.session.commit()
    return redirect(url_for('schedule'))


@app.route('/delete_event/<int:id>')
@login_required
def delete_event(id):
    e = db.session.get(Event, id)
    if e:
        db.session.delete(e)
        db.session.commit()
    return redirect(url_for('schedule'))


# =========================
# Logout
# =========================

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# =========================
# DB Init + Run
# =========================

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
