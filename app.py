from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///participantes.db'
app.config['SECRET_KEY'] = 'moto_clube_secret'
db = SQLAlchemy(app)

class Participante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    motociclista = db.Column(db.String(100), nullable=False)
    moto_clube = db.Column(db.String(100), nullable=False)
    tem_acompanhante = db.Column(db.String(3), nullable=False)
    acompanhante_nome = db.Column(db.String(100))
    cidade = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(2), nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/formulario')
def formulario():
    return render_template('formulario.html')

@app.route('/salvar', methods=['POST'])
def salvar():
    novo = Participante(
        motociclista=request.form['motociclista'],
        moto_clube=request.form['moto_clube'],
        tem_acompanhante=request.form['tem_acompanhante'],
        acompanhante_nome=request.form.get('acompanhante_nome', ''),
        cidade=request.form['cidade'],
        estado=request.form['estado']
    )
    db.session.add(novo)
    db.session.commit()
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    participantes = Participante.query.all()
    total = len(participantes)
    motociclistas = len([p for p in participantes if p.tem_acompanhante == 'Não'])
    acompanhantes = len([p for p in participantes if p.tem_acompanhante == 'Sim'])
    return render_template('dashboard.html', participantes=participantes, total=total, motociclistas=motociclistas, acompanhantes=acompanhantes)

@app.route('/deletar/<int:id>')
def deletar(id):
    p = Participante.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    return redirect('/dashboard')

if __name__ == '__main__':
    app.run(debug=True)
