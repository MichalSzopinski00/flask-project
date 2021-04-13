from flask import render_template, request
from flask.app import Flask
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
app = Flask(__name__)


app.config['SQL_ALCHEMY_DATABASE_URL'] = r"sqlite:///C:\Users\mszopinski\Desktop\zaj\projekt flask\flask_sqlalchemy.db"


db = SQLAlchemy(app)

@app.route('/login')

def user_mangement():
    return render_template('login.html')

@app.route('/register')

def user_add():
    return render_template('user_registration.html')

@app.route('/portal')

def files_1():
    return render_template('portal.html')



if __name__ =="__main__":
    db.create_all()
    app.run(debug=True, port=1234)