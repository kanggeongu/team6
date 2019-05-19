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
from sqlalchemy.orm import query

DEBUG=True
DATABASE='midterm_project.db'
PER_PAGE=20
SECRET_KEY = 'development key'

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('GPSR_SETTINGS', silent=True)

def connect_db():
    setmax={"max":0}
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

def make_dictionary(num):
    q = temp
    a = dict()
    for z in range(num):
        d = query_db('select * from page where page_url = ? order by data_count desc limit ?', [url,20])
        for i in d:
            if i['page_url'] in d:
                d[i['page_url']].append(i['data_noun'])
                d[i['page_url']].append(i['data_count'])
            else:
                lst = []
                lst.append(i['data_noun'])
                lst.append(i['data_count'])
                d = {i['page_url']:lst}
            
    return a

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
    date=int(time.time())
    error=None
    if url == '':
        return render_template('home.html',parsed=None, time=date,error='No page')
    
    res = requests.get(url)
    return res.raise_for_status()
    html=BeautifulSoup(res.content,'html.parser')
    
    if html is None:
        error='No page'
        return render_template('home.html', parsed=None, time=date, error=error)
    
    parsed = html.text
    token=parsed.split()
    tag=nltk.pos_tag(token)
    
    temp=query_db('select * from result where result_url = ?',[url],one=True)
    if temp is None:
        for i, j in tag:
            if not(i.isalnum()):
                continue
            if j == 'NN' or j == 'NNP' or j == 'NNS' or j == 'NNPS':
                chk = query_db('select * from page where (page_url, data_noun) = (?,?)',[url, i],True)
                if chk is None:
                    g.db.execute('insert into page (page_url, data_noun, data_count) values (?,?,?)',[url,i,1])
                    g.db.commit()
                else:
                    n=chk['data_count']
                    g.db.execute('update page set data_count = ? where (page_url, data_noun) = (?,?)',[n+1, url, i])
                    g.db.commit()
    
    temp = query_db('select * from page where page_url = ? order by data_count desc limit ?', [url, 20])
    stra = ''
    for data in temp:
        stra+=data['data_noun']
        stra+=' '
        stra+=str(data['data_count'])
        stra+=' '
    
    g.db.execute('insert into result(result_url, result_ret) values(?,?)',[url, stra])
    g.db.commit()
    
    ret=query_db('select * from result')
    return render_template('home.html', parsed=ret, time=date, error=error)


app.jinja_env.filters['datetimeformat'] = format_datetime

if __name__ == '__main__':
    init_db()
    app.run()
