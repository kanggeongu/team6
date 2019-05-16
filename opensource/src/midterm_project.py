# -*- coding: utf-8 -*-

from datetime import datetime
import time
from sqlite3 import dbapi2 as sqlite3
from flask import Flask,render_template,request, url_for, redirect,g,flash
from bs4 import BeautifulSoup
import requests
from contextlib import closing

DEBUG = True
SECRET_KEY = 'development key'

app = Flask(__name__)

def format_datetime(timestamp):
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d @ %H:%M')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/info', methods=['POST', 'GET'])
def info():
    search=request.form['toSearch']
    url = "https://google.com/search?q="+search
    res = requests.get(url)
    
    html=BeautifulSoup(res.content,'html.parser')
    
    error=None
    
    html_title=html.find(attrs={'class':'r'})
    html_body = html.find(attrs={'class':'st'})
    title=html_title.text
    body=html_body.text
    date=int(time.time())
   
    return render_template('home.html', parsed_title=title, parsed_body=body,time=date,Search=search ,error=error)


app.jinja_env.filters['datetimeformat'] = format_datetime

if __name__ == '__main__':
    app.run()