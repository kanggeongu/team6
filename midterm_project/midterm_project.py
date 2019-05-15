from flask import Flask,render_template,request, url_for, redirect
from bs4 import BeautifulSoup
import requests
app = Flask(__name__)

DEBUG = True
SECRET_KEY = 'development key'

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
    
    return render_template('home.html', parsed_title=title, parsed_body=body, error=error)

if __name__ == '__main__':
    app.run()