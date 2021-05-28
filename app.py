from flask import render_template, request, redirect
from flask.app import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql.expression import column
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import VARCHAR
from sqlalchemy.orm import relationship
from werkzeug.utils import secure_filename 
from pathlib import Path
import matplotlib.pyplot as plt
import os
import pandas as pd
import numpy as np

app = Flask(__name__)

UPLOAD_FOLDER=r"C:\Users\mszopinski\Desktop\zaj\projekt flask\flask-project\files"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = r"sqlite:///C:\Users\mszopinski\Desktop\zaj\projekt flask\flask-project\my.db"

db = SQLAlchemy(app)

class file_details(db.Model):
    __tablename__ = 'file_details'
    id = Column(Integer, primary_key = True, autoincrement = True)
    name = Column(String (100), unique = True, nullable = True)   
    columns = Column(Integer, nullable = True)
    rows = Column(Integer, nullable = True)
    size = Column(Integer, nullable = True)
    one_to_many = relationship('file_specs', backref='file_details', lazy='dynamic') 

class file_specs(db.Model):
    __tablename__ = 'file_specs'
    id = Column(Integer, primary_key = True, autoincrement=True)
    file_details_id = Column(Integer, ForeignKey('file_details.id'),nullable=False)
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
        if request.method == 'GET':
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
                    data = file_details(name = filename,
                                        columns =df.shape[1],
                                        rows = df.shape[0],
                                        size = size)
                    db.session.add(data)
                    db.session.commit() # commit żeby ściągnąć data.id

                    for column in df:
                        if df[column].dtype == "object": # zamien na sile na
                            unique= np.count_nonzero(df[column].unique())
                            null_values = df[column].isnull().sum()
                            nan_values = df[column].isna().sum()
                            file_specs_db = file_specs(column_type = df[column].dtype.name,
                                                        file_details_id = data.id, 
                                                        number_of_unique_values = unique,
                                                        number_of_null_values = int(null_values),
                                                        number_of_nan_values = int(nan_values))
                            db.session.add(file_specs_db)

                        elif df[column].dtype == "int64" or df[column].dtype == "float64":
                            minimum_value = df[column].min()
                            maximum_value = df[column].max()
                            avg_value = df[column].mean()
                            median_value = df[column].median()
                            standard_deviation_value = df[column].std()
                            file_specs_db2 = file_specs(column_type = df[column].dtype.name,
                                                          file_details_id = data.id, 
                                                          min = minimum_value,
                                                          max = maximum_value,
                                                          avg = avg_value,
                                                          median = median_value,
                                                          standard_deviation = standard_deviation_value)
                            db.session.add(file_specs_db2)

                        elif df[column].dtype == "datetime64":
                            first_date_value = df[column].min()
                            last_date_value = df[column].max()
                            file_specs_db3 = file_specs(column_type = df[column].dtype.name,
                                                         file_details_id = data.id,
                                                         first_date = first_date_value,
                                                         last_date = last_date_value)
                            db.session.add(file_specs_db3)

                        elif df[column].dtype == "bool":
                            df[column].value_counts().plot(kind='bar', 
                                                         title='number of bool values') 
                            plt.savefig(f"files\{filename}\{df[column].name}.png")

                        elif df[column].dtype == "Category":
                            df[column].value_counts().plot(kind='bar', 
                                                         title='number of Categorical values') 
                            plt.savefig(f"files\{filename}\{df[column].name}.png")
                    try: 
                        db.session.commit() 
                    except:
                        db.session.rollback()
                        return "niestety taki rekord już istnieje w bazie danych najpierw usuń dane z bazy i spróbuj ponownie"
                    
                    return redirect("/summary")
            
            else:    
                return render_template('error1.html')

@app.route('/summary',methods=['GET'])

def summary():
    return render_template("portalSummary.html")

@app.route('/specific_file',methods=['GET'])

def your_files():
    print("y tho")
    
if __name__ =="__main__":
    db.create_all()
    app.run(debug=True, port=1234)