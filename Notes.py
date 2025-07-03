from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask import Flask
from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Optional


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:WoMyCWgVJaTGCpJUtQQRKasAgWuoEsWY@shinkansen.proxy.rlwy.net:23068/railway'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    notes = db.relationship('Note', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    mood = db.Column(db.String(50), nullable=True)  # New mood field
    
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='note', lazy=True, cascade='all, delete-orphan')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    note_id = db.Column(db.Integer, db.ForeignKey('note.id'), nullable=False)

app.secret_key = 'secret_key_lhrba_492'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect('/notes')
        else:
            return "Invalid credentials", 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/notes', methods=['GET', 'POST'])
def notes():
    if 'user_id' not in session:
        return redirect('/login')

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        content = request.form['content']
        mood = request.form.get('mood', 'neutral')  # Get mood from form
        if content.strip():
            new_note = Note(content=content, author_id=user.id, mood=mood,timestamp=datetime.utcnow() + timedelta(hours=1))  # type: ignore
            db.session.add(new_note)
            db.session.commit()
            flash('Note added!')
            return redirect('/notes')
        else:
            flash('Note content cannot be empty.')

    notes = Note.query.order_by((Note.timestamp + timedelta(hours=1)).desc()).all()
    return render_template('notes.html', user=user, notes=notes)

@app.route('/add_comment', methods=['POST'])
def add_comment():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    note_id = request.form.get('note_id')
    content = request.form.get('content')
    
    # Check if required fields are present
    if not note_id:
        return jsonify({'error': 'Note ID is required'}), 400
    
    if not content:
        return jsonify({'error': 'Comment content is required'}), 400
    
    if not content.strip():
        return jsonify({'error': 'Comment cannot be empty'}), 400
    
    try:
        note_id_int = int(note_id)
    except ValueError:
        return jsonify({'error': 'Invalid note ID'}), 400
    
    note = Note.query.get(note_id_int)
    if not note:
        return jsonify({'error': 'Note not found'}), 404
    
    new_comment = Comment(content=content.strip(), author_id=user.id, note_id=note_id_int)  # type: ignore
    db.session.add(new_comment)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'comment': {
            'id': new_comment.id,
            'content': new_comment.content,
            'timestamp': (new_comment.timestamp + timedelta(hours=1)).strftime('%b %d, %Y at %H:%M'),
            'author': user.username,
            'author_avatar': user.username[0].upper()
        }
    })

@app.route('/')
def home():
    return redirect('/login')

if __name__ == "__main__":
       
    with app.app_context():
        if not User.query.filter_by(username='Abderrahmane').first():
            user1 = User(username='Abderrahmane', password=generate_password_hash('ZeroTwo02'))  # type: ignore
            db.session.add(user1)

        if not User.query.filter_by(username='Ikram').first():
            user2 = User(username='Ikram', password=generate_password_hash('Bibibobo1loop2'))  # type: ignore
            db.session.add(user2)
        

        db.session.commit()
        db.create_all()
        print("MySQL database tables created!")
    app.run(debug=False, host="0.0.0.0", port=8000)