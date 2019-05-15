from flask import Flask,render_template,request, url_for, redirect
from bs4 import BeautifulSoup
import requests
app = Flask(__name__)

DEBUG = True
SECRET_KEY = 'development key'

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/info', methods=['POST'])
def info():
    search=request.form['toSearch']
    url = "https://namu.wiki/w/"+search
    res = requests.get(url)
    
    html=BeautifulSoup(res.content,'html.parser')
    
    html_title=html.find('title')
    html_body = html.find(attrs={'class':'wiki-paragraph'})
    
    title=html_title.text
    body=html_body.text
    
    return redirect(url_for('home', parsed_title=title, parsed_body=body))

if __name__ == '__main__':
    app.run()