from flask import Flask, render_template_string, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    level = db.Column(db.Integer, default=1)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    questions = db.relationship('Question', backref='quiz', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    text = db.Column(db.String(200), nullable=False)

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    text = db.Column(db.String(200), nullable=False)

# --- Decorators ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(level):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('level', 0) < level: flash('Acesso negado!'); return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- HTML Templates ---
BASE_TEMPLATE = """
<!DOCTYPE html><html lang='pt-br'><head><link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css' rel='stylesheet'><title>Sistema Profissional</title></head>
<body><nav class='navbar navbar-expand-lg navbar-dark bg-dark'><div class='container'><a class='navbar-brand' href='/'>Sistema</a><div class='navbar-nav'><a class='nav-link' href='/dashboard'>Dashboard</a><a class='nav-link' href='/logout'>Sair</a></div></div></nav>
<div class='container mt-4'>{% with messages = get_flashed_messages() %}{% if messages %}{% for m in messages %}<div class='alert alert-info'>{{m}}</div>{% endfor %}{% endif %}{% endwith %}{% block content %}{% endblock %}</div></body></html>
"""

# --- Routes ---
@app.route('/')
def index(): return render_template_string(BASE_TEMPLATE + "<h1>Bem-vindo</h1><a href='/login' class='btn btn-primary'>Login</a>")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id; session['level'] = user.level; return redirect(url_for('dashboard'))
        flash('Credenciais inválidas')
    return render_template_string(BASE_TEMPLATE + "<form method='POST'><input name='username' class='form-control mb-2' placeholder='Usuário'><input type='password' name='password' class='form-control mb-2' placeholder='Senha'><button class='btn btn-success'>Entrar</button></form>")

@app.route('/dashboard')
@login_required
def dashboard(): return render_template_string(BASE_TEMPLATE + "<h1>Dashboard</h1><div class='list-group'><a href='/listar-clientes' class='list-group-item'>Clientes</a><a href='/listar-questionarios' class='list-group-item'>Questionários</a>{% if session.level == 3 %}<a href='/usuarios' class='list-group-item'>Gerenciar Usuários</a>{% endif %}</div>")

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('index'))

@app.route('/listar-clientes')
@login_required
def listar_clientes():
    clientes = Client.query.all()
    return render_template_string(BASE_TEMPLATE + "<h1>Clientes</h1><ul>{% for c in clientes %}<li>{{c.name}}</li>{% endfor %}</ul><a href='/cadastro-cliente' class='btn btn-primary'>Novo</a>", clientes=clientes)

@app.route('/cadastro-cliente', methods=['GET', 'POST'])
@login_required
def cadastro_cliente():
    if request.method == 'POST':
        db.session.add(Client(name=request.form['name'], email=request.form['email'])); db.session.commit(); return redirect(url_for('listar_clientes'))
    return render_template_string(BASE_TEMPLATE + "<form method='POST'><input name='name' class='form-control mb-2' placeholder='Nome'><input name='email' class='form-control mb-2' placeholder='Email'><button class='btn btn-primary'>Salvar</button></form>")

@app.route('/usuarios')
@login_required
@role_required(3)
def listar_usuarios():
    users = User.query.all()
    return render_template_string(BASE_TEMPLATE + "<h1>Usuários</h1><table class='table'>{% for u in users %}<tr><td>{{u.username}}</td><td>Nível {{u.level}}</td><td><a href='/usuario/{{u.id}}/editar'>Editar</a></td></tr>{% endfor %}</table><a href='/usuario/novo' class='btn btn-success'>Novo</a>", users=users)

@app.route('/usuario/novo', methods=['GET', 'POST'])
@login_required
@role_required(3)
def novo_usuario():
    if request.method == 'POST':
        db.session.add(User(username=request.form['username'], password=generate_password_hash(request.form['password']), level=int(request.form['level']))); db.session.commit(); return redirect(url_for('listar_usuarios'))
    return render_template_string(BASE_TEMPLATE + "<form method='POST'><input name='username' class='form-control mb-2' placeholder='User'><input type='password' name='password' class='form-control mb-2' placeholder='Senha'><input name='level' type='number' class='form-control mb-2' placeholder='Nível (1-3)'><button class='btn btn-primary'>Criar</button></form>")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='Wesley').first():
            db.session.add(User(username='Wesley', password=generate_password_hash('123'), level=3))
            db.session.commit()
    app.run(debug=True)