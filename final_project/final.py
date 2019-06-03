# -*- coding: utf-8 -*-
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, url_for, redirect, \
     render_template, g
from bs4 import BeautifulSoup
from contextlib import closing
from werkzeug.security import check_password_hash, generate_password_hash

DEBUG=True
DATABASE="final_project.db"
PER_PAGE=20

SECRET_KEY = 'development key'

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('GPSR_SETTINGS', silent=True)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv

@app.before_request
def before_request():
    g.db = connect_db()
    g.user = None
    if 'user_num' in session:
        g.user = query_db('select * from user where user_num = ?',
                          [session['user_num']], one=True)

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

def get_user_num(id):
    chk = g.db.execute('select user_num from user where user_id = ?', [id]).fetchone()
    if chk is not None:
        return chk[0]
    else:
        return None

@app.route('/register', methods=['GET','POST'])
def register():
    error=None
    if request.method == 'POST':
        if not request.form['id']:
            error='You have to enter a id'
        elif not request.form['password']:
            error='You have to enter a password'
        elif not request.form['password2']:
            error='You have to enter a password'
        elif request.form['password']!=request.form['password2']:
            error='Passwords not match'
        elif get_user_num(request.form['id']) is not None:
            error='The id is already taken'
        else:
            g.db.execute('insert into user(user_id, user_pw_hash) values(?, ?)',
                [request.form['id'], generate_password_hash(request.form['password'])])
            g.db.commit()
            return redirect(url_for('login'))
    return render_template('register.html', error=error)


@app.route('/login', methods=['GET','POST'])
def login():
    error=None
    if request.method == 'POST':
        user=query_db('select * from user where user_id = ?', [request.form['id']], one=True)
        if user is None:
            error = 'Invalid username'
        elif not check_password_hash(user['user_pw_hash'], 
                                     request.form['password']):
            error = 'Invalid password'
        else:
            session['user_num']=user['user_num']
            return redirect(url_for('home'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('user_num', None)
    return redirect(url_for('home'))


@app.route('/')
def home():
    user=None
    if g.user:
        user = g.user['user_id']
    return render_template('home.html',user=user)


if __name__ == '__main__':
    init_db()
    app.run()