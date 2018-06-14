from flask import Flask, render_template, flash, redirect, url_for, request, g, session
from wtforms import Form, validators, StringField
from werkzeug.utils import secure_filename
import sqlite3
from functools import wraps
import os
import pandas as pd

app = Flask(__name__)
UPLOAD_FOLDER = 'Uploads'
if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
assert os.path.exists('AppSecretKey.txt'), "Unable to locate app secret key"
with open('AppSecretKey.txt','r') as f:
    key=f.read()
app.secret_key=key
assert os.path.exists('users.db'), "Unable to locate users.db database"
assert os.path.exists('files.db'), "Unable to locate files.db database"

#Set subdomain...
#If running locally (or index is the domain) set to blank, i.e. subd=""
#If index is a subdomain, set as appropriate *including* leading slash, e.g. subd="/WCSSP-FORTIS"
#Routes in @app.route() should NOT include subd, but all other references should...
#Use redirect(subd + '/route') rather than redirect(url_for(route))
#Pass subd=subd into every render_template so that it can be used to set the links appropriately
#
subd=""

#Connect to DB
def get_db(DBname):
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DBname)
        db.row_factory = sqlite3.Row
    return db

#Close DB if app stops
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

#Query DB
def query_db(DBname,query,args=(),one=False):
    cur = get_db(DBname).execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else (rv if rv else None)

#Query DB pandas
def pandas_db(DBname,query):
    db = get_db(DBname)
    df = pd.read_sql_query(query,db)
    db.close()
    return df

#Check if user is logged in (either as a trainer or a trainee)
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorised, please login', 'danger')
            return redirect(subd+'/')
    return wrap

#Check if user is logged in as a trainer
def is_logged_in_as_trainer(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session and session['usertype']=='trainer':
            return f(*args, **kwargs)
        else:
            flash('Unauthorised, please login as a trainer', 'danger')
            return redirect(subd+'/')
    return wrap

#Index
@app.route('/', methods=["GET","POST"])
def index():
    if request.method == 'POST':
        #Get form fields
        username = request.form['username']
        password_candidate = request.form['password']
        result = query_db('users.db', 'SELECT * FROM users WHERE username = ?', [username])
        if result is not None:
            data = query_db('users.db', 'SELECT * FROM users WHERE username = ?', [username], one=True)
            password = data['password']
            usertype = data['usertype']
            #Compare passwords
            if password_candidate == password:
                #Passed
                session['logged_in'] = True
                session['username'] = username
                session['usertype'] = usertype
                flash('You are now logged in', 'success')
                return redirect(subd+'/')
            else:
                flash('Incorrect password', 'danger')
                return redirect(subd+'/')
        else:
            flash('Username not found', 'danger')
            return redirect(subd+'/')
    return render_template('home.html',subd=subd)

@app.route('/training-material')
@is_logged_in
def training_material():
    return render_template('training-material.html',subd=subd)

@app.route('/trainer-material')
@is_logged_in_as_trainer
def trainer_material():
    return render_template('trainer-material.html',subd=subd)

class UploadForm(Form):
    title = StringField(u'Title of material',[validators.Length(min=1,max=50)])

@app.route('/upload', methods=["GET","POST"])
@is_logged_in_as_trainer
def upload():
    form = UploadForm(request.form)
    #If user tries to upload a file
    if request.method == 'POST' and form.validate():
        #Get file info
        newfile = request.files['file']
        #No selected file
        if newfile.filename == '':
            flash('No file selected','danger')
            return redirect(subd+'/upload')
        #Upload file
        else:
            filename = secure_filename(newfile.filename)
            newfile.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('File uploaded', 'success')
            return redirect(subd+'/upload')
    #If user just navigates to page
    return render_template('upload.html',subd=subd,form=form)

#Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(subd+'/')

if __name__ == '__main__':
    app.run(debug=True)
