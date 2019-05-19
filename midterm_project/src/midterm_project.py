# -*- coding: utf-8 -*-
from datetime import datetime
import time
from sqlite3 import dbapi2 as sqlite3
from flask import Flask,render_template, request, url_for, redirect, g, flash
from bs4 import BeautifulSoup
import requests
from contextlib import closing
from nltk import regexp_tokenize
import nltk


DEBUG=True
DATABASE='midterm_project.db'
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

@app.teardown_request
def teardown_request(exception):
    g.db.close()

def format_datetime(timestamp):
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d @ %H:%M')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/info', methods=['POST', 'GET'])
def info():
    url = request.form['url']
    res = requests.get(url)
    html=BeautifulSoup(res.content,'html.parser')
    error=None
    date=int(time.time())
    if html is None:
        error='No page'
        return render_template('home.html', parsed=None, time=date, error=error)
    parsed = html.text
    token=parsed.split()
    tag=nltk.pos_tag(token)
    for i, j in tag:
        if j == 'NN' or j == 'NNP' or j == 'NNS' or j == 'NNPS':
            chk = query_db('select * from page where (page_url, data_noun) = (?,?)',[url, i],True)
            if chk is None:
                g.db.execute('insert into page (page_url, data_noun, data_count) values (?,?,?)',[url,i,1])
                g.db.commit()
            else:
                n=chk['data_count']
                g.db.execute('update page set data_count = ? where (page_url, data_noun) = (?,?)',[n+1, url, i])
    
    ret=query_db('select data_noun, data_count from page order by data_count desc limit ?', [PER_PAGE])
    return render_template('home.html', parsed=ret, time=date, error=error)


app.jinja_env.filters['datetimeformat'] = format_datetime

if __name__ == '__main__':
    init_db()
    app.run()