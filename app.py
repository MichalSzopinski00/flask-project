from flask import render_template, request, redirect,url_for
from flask.app import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import VARCHAR
from sqlalchemy.orm import relationship, Session
from werkzeug.utils import secure_filename 
from pathlib import Path
import matplotlib.pyplot as plt
import os
import pandas as pd
import numpy as np
import shutil


app = Flask(__name__,static_folder="files")

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
    def __repr__(self):
        return f'{self.name}'

class file_specs(db.Model):
    __tablename__ = 'file_specs'
    id = Column(Integer, primary_key = True, autoincrement=True)
    file_details_id = Column(Integer, ForeignKey('file_details.id'), nullable=False)
    column_name = Column(VARCHAR(30), nullable = True)
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
    number_of_nan_values = Column(Integer(),nullable=True)

@app.route('/',methods=['GET', 'POST'])

def portal():
    try:
        if request.method == 'GET':
            return render_template('portal.html')

        elif request.method == 'POST':
            f = request.files['file'] 
            df = pd.read_csv(f,sep=";")

            if df.shape[0] < 1000 and df.shape[1] < 20:

                filename = secure_filename(f.filename) 
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
                                        columns = df.shape[1],
                                        rows = df.shape[0],
                                        size = size)
                    db.session.add(data)
                    db.session.commit() 

                    for column in df:
                        if df[column].dtype == "object": # zamien na sile na datetime 64
                            unique= np.count_nonzero(df[column].unique())
                            null_values = df[column].isnull().sum()
                            nan_values = df[column].isna().sum()
                            file_specs_db = file_specs(column_type = df[column].dtype.name,
                                                        column_name=df[column].name,
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
                                                          column_name=df[column].name,
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
                                                         column_name=df[column].name,
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
    except:
        return render_template('error.html')

@app.route('/summary',methods=['GET'])

def summary():
    print(file_details.query.all())
    return render_template("portalSummary.html",\
                            s = file_details.query.all(),\
                            len = file_details.query.count())

@app.route('/specific_file/<filename>',methods=['GET'])

def specific_file(filename):
    try:
        get_id = file_details.query\
            .filter(file_details.name == filename)
        for x in get_id:
            current_id = x.id

        ORM_query = file_specs.query\
            .join(file_details, file_specs.file_details_id == file_details.id)\
            .filter(file_specs.file_details_id == current_id)

        df = pd.read_csv(f'files/{filename}/{filename}')
        list_of_histograms = []
        for column in df:
            if os.path.exists(f'files/{filename}/{df[column].name}.png'):
                print (f"File {df[column].name}.png exist")
                list_of_histograms.append(f'{df[column].name}.png')
                
            else:
                pass
        len_list = len(list_of_histograms)
        return render_template("portalfinal.html",userList = ORM_query,\
                                    list = list_of_histograms,\
                                    filename = filename,\
                                    len_list = len_list)
    except:
        return render_template("file_does_not_exist.html")

@app.route('/drop_file/<filename>',methods = ['GET'])

def drop_file(filename):
    try:
        get_id = file_details.query\
            .filter(file_details.name == filename)\

        for y in get_id:
            current_id = y.id

        file_specs.query\
            .filter(file_specs.file_details_id == current_id)\
            .delete()
            
        file_details.query\
            .filter(file_details.name == filename)\
            .delete()

        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        shutil.rmtree(path)
        
        db.session.commit()
        return render_template("portalDeleteFile.html")
    except:
        db.session.rollback()
        return render_template("error_unfinished_drop.html")
    
if __name__ =="__main__":
    db.create_all()
    app.run(debug=True, port=1234)