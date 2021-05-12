from flask import render_template, request
from flask.app import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, DateTime
import pandas as pd
from sqlalchemy.sql.expression import column
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import VARCHAR
from werkzeug.utils import secure_filename #zapis do pliku 
import os
from pathlib import Path

app = Flask(__name__)

UPLOAD_FOLDER=r"C:\Users\mszopinski\Desktop\zaj\projekt flask\flask-project\files"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = r"sqlite:///C:\Users\mszopinski\Desktop\zaj\projekt flask\flask-project\my.db"

db = SQLAlchemy(app)

class file_details(db.Model):
    __tablename__ = 'file_details'
    id = Column(Integer, primary_key = True, autoincrement = True)
    name = Column(String (100), unique = True,nullable = True)   
    columns = Column(Integer, nullable = True)
    rows = Column(Integer, nullable = True)
    size = Column(Integer, nullable = True)
    def __repr__(self): # co  wywal to :)
        return f'<Nazwa_pliku: {self.name},\
             Ilosc_kolumn: {self.columns},\
                Ilosc_wierszy: {self.rows}>'

class file_specs(db.Model):
    __tablename__ = 'file_specs'
    id = Column(Integer, primary_key = True, autoincrement=True)
    file_details_id = Column(Integer,ForeignKey(file_details.id))
    column_type = Column(VARCHAR(30), nullable = True)
    min = Column(Float(),nullable=True)
    max = Column(Float(),nullable=True)
    avg = Column(Float(),nullable=True)
    median = Column(Float(),nullable=True)
    standard_deviation = Column(Float(),nullable=True)
    first_date = Column(DateTime(),nullable=True)
    last_date = Column(DateTime(),nullable=True)
    number_of_unique_values = Column(Integer(),nullable=True)
    number_of_null_values = Column(Integer(),nullable=True)
    number_of_nan_values =Column(Integer(),nullable=True)

@app.route('/',methods=['GET', 'POST'])

def portal():
        if request.method =='GET':
            return render_template('portal.html')

        elif request.method == 'POST':
            f = request.files['file'] 
            df = pd.read_csv(f)

            if df.shape[0] < 1000 and df.shape[1] < 20:

                filename = secure_filename(f.filename) #zapis do pliku
                path = r'C:\Users\mszopinski\Desktop\zaj\projekt flask\flask-project\files\{}'.format(filename)
                dir_with_name=os.path.join(path, filename)
                my_file = Path(dir_with_name)

                if my_file.exists():
                    return "taki plik już istnieje"
                
                else:
                    os.makedirs(r'C:\Users\mszopinski\Desktop\zaj\projekt flask\flask-project\files\{}'.format(filename))
                    f.save(dir_with_name)
                    df.to_csv(dir_with_name)
                    size=os.stat(dir_with_name).st_size
                    data = file_details(name = filename, columns =df.shape[1], rows = df.shape[0], size = size) # baza danych
                    db.session.add(data)

                    try: # sprawdzenie poprawności jeśli ok wprowadź dane jeśli nie wycofaj
                        db.session.commit() 
                    except:
                        db.session.rollback()
                        return "niestety taki rekord już istnieje w bazie danych najpierw usuń dane z bazy i spróbuj ponownie"
                    
                    return render_template('portalAfterImport.html',shape=df.shape)
            
            else:    
                return render_template('error1.html')

if __name__ =="__main__":
    db.create_all()
    app.run(debug=True, port=1234)