# -*- coding: utf-8 -*-
from sqlite3 import dbapi2 as sqlite3
from flask import Flask,render_template, request, url_for, redirect, g
from bs4 import BeautifulSoup
import requests
from contextlib import closing
from nltk import regexp_tokenize
from nltk.corpus import stopwords
import nltk
import re
from sqlalchemy.orm import query
from math import sqrt

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

def make_dictionary(num):
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


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/info', methods=['POST', 'GET'])
def info():
    url = request.form['url']
    error=None
    if url == '':
        return render_template('home.html',parsed=query_db('select * from result'), error='No input')
    
    res = requests.get(url)
    html=res.content
    
    tokens=re.split('\W+',html.decode('utf-8'))
    clean=BeautifulSoup(html,'html.parser').get_text()
    
    tokens=[tok for tok in clean.split()]
    clean=BeautifulSoup(html,'html.parser')

    for script in clean(["script", "style"]):
        script.extract()

    text=clean.get_text()
    
    tokens=[tok for tok in text.split()]
    stop=set(stopwords.words('english'))
    
    clean_tokens = [tok for tok in tokens if len(tok.lower())>1 and (tok.lower() not in stop)]
    tags=nltk.pos_tag(clean_tokens)
    
    tag = [i for i,j in tags if j in ['NN', 'NNP', 'NNS', 'NNPS']]
    
    temp=query_db('select * from result where result_url = ?',[url],one=True)
    if temp is None:
        for i in tag:
            if not(i.isalnum()):
                continue
            chk = query_db('select * from page where (page_url, data_noun) = (?,?)',[url, i],True)
            if chk is None:
                g.db.execute('insert into page (page_url, data_noun, data_count) values (?,?,?)',[url,i,1])
                g.db.commit()
            else:
                n=chk['data_count']
                g.db.execute('update page set data_count = ? where (page_url, data_noun) = (?,?)',[n+1, url, i])
                g.db.commit()
    
    temp=query_db('select * from page where page_url = ? order by data_count desc', [url])
    strb= ''
    for data in temp:
        strb+=data['data_noun']
        strb+=' '
        strb+=str(data['data_count'])
        strb+=' '
    
    temp = query_db('select * from page where page_url = ? order by data_count desc limit ?', [url, 20])
    stra = ''
    for data in temp:
        stra+=data['data_noun']
        stra+=' '
        stra+=str(data['data_count'])
        stra+=' '
    
    g.db.execute('insert into result(result_url, result_ret, result_cal) values(?,?,?)',[url, stra, strb])
    g.db.commit()
    
    ret=query_db('select * from result')
    return render_template('home.html', parsed=ret, error=error)

@app.route('/report', methods=['POST', 'GET'])
def report():
    li=[]
    newli=[]
    temp=query_db('select * from result')
    c=0
    d=0
    for i in temp:
        for j in temp:
            count=0
            match=0
            stI=i['result_cal'].split(' ')
            stJ=j['result_cal'].split(' ')
            lenI=len(stI)-1
            lenJ=len(stJ)-1
            
            for idxI in range(0,lenI,2):
                count += int(stI[idxI+1])
                
                for idxJ in range(0,lenJ,2):
                    if stI[idxI] == stJ[idxJ]:
                        match += int(stJ[idxJ+1])
                        break
                    
            for idxJ in range(0,lenJ,2):
                count += int(stJ[idxJ+1])
               
            li.append([count-match,match,d])
            d+=1
        c += 1
    return render_template('report.html',li=li,count=c)

@app.route('/delete', methods=['POST', 'GET'])
def delete():
    g.db.execute('delete from result')
    g.db.execute('delete from page')
    g.db.commit()
    return redirect(url_for('home'))

@app.route('/delete_one/<id>', methods=['POST', 'GET'])
def delete_one(id):
    #temp = query_db('select * from result where result_id=?',[id],True)
    #g.db.execute('delete from page where page_url=?',[temp['result_url']])
    g.db.execute('delete from result where result_id=?',[id])
    g.db.commit()
    return render_template('home.html',parsed=query_db('select * from result'),error='deleted')


if __name__ == '__main__':
    init_db()
    app.run()
