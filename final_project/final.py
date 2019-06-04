# -*- coding: utf-8 -*-
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, url_for, redirect, \
     render_template, g
from bs4 import BeautifulSoup
from contextlib import closing
from werkzeug.security import check_password_hash, generate_password_hash
import requests
import json

app = Flask(__name__)
app.config.from_pyfile('config.py')

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
    url="https://comic.naver.com/webtoon/weekday.nhn"
    res = requests.get(url)
    html = BeautifulSoup(res.content,'html.parser')
    list_area = html.find(attrs={'class':'list_area daily_all'})
    list_area_image=list_area.find_all('img')
    list_area_title=list_area.find_all(attrs={'class':'title'})
    
    naver_title=[]
    naver_link=[]
    naver_image=[]
    for i in list_area_title:
        title = i.get('title')
        link = i.get('href')
        if title is not None:
            naver_title.append(title)
        if link is not None:
            naver_link.append('https://comic.naver.com'+link)
    for i in list_area_image:
        title = i.get('title')
        img = i.get('src')
        if title is not None:
            naver_image.append(img)
    nlength = len(naver_title)
    
    durl=[]
    durl.append("http://webtoon.daum.net/data/pc/webtoon/list_serialized/mon")
    durl.append("http://webtoon.daum.net/data/pc/webtoon/list_serialized/tue")
    durl.append("http://webtoon.daum.net/data/pc/webtoon/list_serialized/wed")
    durl.append("http://webtoon.daum.net/data/pc/webtoon/list_serialized/thu")
    durl.append("http://webtoon.daum.net/data/pc/webtoon/list_serialized/fri")
    durl.append("http://webtoon.daum.net/data/pc/webtoon/list_serialized/sat")
    durl.append("http://webtoon.daum.net/data/pc/webtoon/list_serialized/sun")
    
    daum_title=[]
    daum_link=[]
    daum_image=[]
    for i in range(7):
        res = requests.get(durl[i])
        data= res.content
        
        j = json.loads(data)
        k = j["data"]
        for l in k:
            daum_title.append(l['title'])
            nickname = l['nickname']
            p = l['thumbnailImage2']
            imagelink = p['url']
            daum_link.append('http://webtoon.daum.net/webtoon/view/'+nickname)
            daum_image.append(imagelink)
            
    wt_link=naver_link+daum_link
    wt_title=naver_title+daum_title
    wt_image=naver_image+daum_image
    dlength = len(daum_link)
    #dlength=134 nlength=263
    return render_template('home.html',
                    user=g.user,wt_link=wt_link,wt_title=wt_title,wt_image=wt_image,nlength=nlength, dlength=dlength)

@app.route('/subscribe', methods=['GET', 'POST'])
def subscribe():
    if not g.user:
        return redirect(url_for('home'))
    link=request.args.get('link')
    image=request.args.get('image')
    title=request.args.get('title')
    user=g.user['user_id']
    g.db.execute('insert into subscribe(sub_link, sub_image, sub_title, sub_user_id) values(?,?,?,?)',
                 [link,image,title,user])
    g.db.commit()
    return redirect(url_for('home'))
    

@app.route('/sub_view')
def sub_view():
    temp = query_db('select * from subscribe')
    return render_template('sub_view.html', a=temp)

if __name__ == '__main__':
    init_db()
    app.run()