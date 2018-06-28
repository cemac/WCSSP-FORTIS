from flask import Flask, render_template, flash, redirect, url_for, request, g, session, abort, send_from_directory
from wtforms import Form, validators, StringField, TextAreaField, SelectField
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
DATABASE = 'FORTIS.db'
assert os.path.exists(DATABASE), "Unable to locate database"

#Set subdomain...
#If running locally (or index is the domain) set to blank, i.e. subd=""
#If index is a subdomain, set as appropriate *including* leading slash, e.g. subd="/WCSSP-FORTIS"
#Routes in @app.route() should NOT include subd, but all other references should...
#Use redirect(subd + '/route') rather than redirect(url_for(route))
#Pass subd=subd into every render_template so that it can be used to set the links appropriately
#
subd=""

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else (rv if rv else None)

#Query DB pandas
def pandas_db(query):
    db = get_db()
    df = pd.read_sql_query(query,db)
    return df

#Insert entry into DB and return the row id
def insert_db(query,args=()):
    db = get_db()
    cur = db.cursor()
    cur.execute(query, args)
    db.commit()
    id = cur.lastrowid
    cur.close()
    return id

#Delete entry from DB
def delete_db(query,args=()):
    db = get_db()
    cur = db.cursor()
    cur.execute(query, args)
    db.commit()
    cur.close()
    return

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

#Get list of workshops from workshop DB:
def get_workshop_list():
    workshopDF = pandas_db('SELECT * FROM workshops')
    workshopList=[('blank','--Please select--')]
    for w in workshopDF['workshop']:
        workshopList.append((w,w))
    return workshopList

def get_ext(filename):
    if '.' in filename:
        ext = '.' + filename.rsplit('.')[-1]
    else:
        ext = ''
    return ext

#Index
@app.route('/', methods=["GET","POST"])
def index():
    if request.method == 'POST':
        #Get form fields
        username = request.form['username']
        password_candidate = request.form['password']
        result = query_db('SELECT * FROM users WHERE username = ?', [username])
        if result is not None:
            data = query_db('SELECT * FROM users WHERE username = ?', [username], one=True)
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

@app.route('/about')
def about():
    return render_template('about.html',subd=subd)

class TimetableForm(Form):
    workshop = SelectField(u'Select the workshop that this timetable is for',\
        [validators.NoneOf(('blank'),message='Please select')])

@app.route('/timetables', methods=["GET","POST"])
@is_logged_in
def timetables():
    form = TimetableForm(request.form)
    form.workshop.choices = get_workshop_list()
    timetablesData = pandas_db('SELECT * FROM timetables')
    #If user tries to upload a timetable
    if request.method == 'POST' and form.validate():
        #Get file name
        newfile = request.files['file']
        #No selected file
        if newfile.filename == '':
            flash('No file selected','danger')
            return redirect(subd+'/timetables')
        #Get fields from web-form
        filename = secure_filename(newfile.filename)
        workshop = form.workshop.data
        #Delete old timetable from database if it exists:
        result = query_db('SELECT * FROM timetables WHERE workshop = ?',(workshop,))
        if result is not None:
            delete_db("DELETE FROM timetables WHERE workshop = ?",(workshop,))
        #Insert new timetable into database:
        id = insert_db("INSERT INTO timetables(filename,workshop) VALUES(?,?)",(filename,workshop))
        #Upload file, calling it <id>_timetable.<ext>:
        ext = get_ext(filename)
        newfile.save(os.path.join(app.config['UPLOAD_FOLDER'],str(id)+'_timetable'+ext))
        #flash success message and reload page
        flash('Timetable uploaded successfully', 'success')
        return redirect(subd+'/timetables')
    return render_template('timetables.html',subd=subd,form=form,timetablesData=timetablesData)

@app.route('/training-material')
@is_logged_in
def training_material():
    filesData = pandas_db('SELECT * FROM files')
    workshopDF = pandas_db('SELECT * FROM workshops')
    workshopList = workshopDF['workshop'].values.tolist()
    return render_template('material.html',subd=subd,filesData=filesData,workshopList=workshopList,who='trainees')

@app.route('/partners')
def partners():
    return render_template('partners.html',subd=subd)

@app.route('/contact-us')
def contact_us():
    return render_template('contact-us.html',subd=subd)

@app.route('/trainer-material')
@is_logged_in_as_trainer
def trainer_material():
    filesData = pandas_db('SELECT * FROM files')
    workshopDF = pandas_db('SELECT * FROM workshops')
    workshopList = workshopDF['workshop'].values.tolist()
    return render_template('material.html',subd=subd,filesData=filesData,workshopList=workshopList,who='trainers')

class UploadForm(Form):
    title = StringField(u'Title of material',[validators.required(),validators.Length(min=1,max=50)])
    description = TextAreaField(u'Description of material',[validators.optional(),validators.Length(max=1000)])
    workshop = SelectField(u'Select the workshop that this material is for',\
        [validators.NoneOf(('blank'),message='Please select')])
    type = SelectField('Select the type of material you are uploading',\
        [validators.NoneOf(('blank'),message='Please select')],\
        choices=[('blank','--Please select--'),
        ('lectures1', 'Lectures (Day 1)'),\
        ('lectures2', 'Lectures (Day 2)'),\
        ('lectures3', 'Lectures (Day 3)'),\
        ('lectures4', 'Lectures (Day 4)'),\
        ('lectures5', 'Lectures (Day 5)'),\
        ('practicals1', 'Practicals (Day 1)'),\
        ('practicals2', 'Practicals (Day 2)'),\
        ('practicals3', 'Practicals (Day 3)'),\
        ('practicals4', 'Practicals (Day 4)'),\
        ('practicals5', 'Practicals (Day 5)'),\
        ('other', 'Other')])
    who = SelectField('Is the material for trainees (typically non-editable files, e.g. PDFs) or trainers (typically editable files, e.g. PPTs)',\
        [validators.NoneOf(('blank'),message='Please select')],\
        choices=[('blank','--Please select--'),
        ('trainees', 'Trainees'),\
        ('trainers', 'Trainers')])

@app.route('/upload', methods=["GET","POST"])
@is_logged_in_as_trainer
def upload():
    form = UploadForm(request.form)
    form.workshop.choices = get_workshop_list()
    #If user tries to upload a file
    if request.method == 'POST' and form.validate():
        #Get file name
        newfile = request.files['file']
        #No selected file
        if newfile.filename == '':
            flash('No file selected','danger')
            return redirect(subd+'/upload')
        #Get fields from web-form
        filename = secure_filename(newfile.filename)
        title = form.title.data
        description = form.description.data
        workshop = form.workshop.data
        type = form.type.data
        who = form.who.data
        #Insert into files database:
        id = insert_db("INSERT INTO files(filename,title,description,workshop,type,who) VALUES(?,?,?,?,?,?)",(filename,title,description,workshop,type,who))
        #Upload file, calling it <id>.<ext>:
        ext = get_ext(filename)
        newfile.save(os.path.join(app.config['UPLOAD_FOLDER'],str(id)+ext))
        #flash success message and reload page
        flash('File uploaded successfully', 'success')
        return redirect(subd+'/upload')
    #If user just navigates to page
    return render_template('upload.html',subd=subd,form=form)

#Download file
@app.route('/download/<string:id>', methods=['POST'])
@is_logged_in
def download(id):
    filename = query_db('SELECT * FROM files WHERE id = ?',(id,),one=True)['filename']
    ext = get_ext(filename)
    filepath = os.path.join(UPLOAD_FOLDER,id+ext)
    if os.path.exists(filepath):
        return send_from_directory(UPLOAD_FOLDER,id+ext,as_attachment=True,attachment_filename=filename)
    else:
        abort(404)

#Download timetable
@app.route('/download-timetable/<string:id>', methods=['POST'])
@is_logged_in
def download_timetable(id):
    filename = query_db('SELECT * FROM timetables WHERE id = ?',(id,),one=True)['filename']
    ext = get_ext(filename)
    filepath = os.path.join(UPLOAD_FOLDER,id+'_timetable'+ext)
    if os.path.exists(filepath):
        return send_from_directory(UPLOAD_FOLDER,id+'_timetable'+ext,as_attachment=True,attachment_filename=filename)
    else:
        abort(404)

#Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(subd+'/')

if __name__ == '__main__':
    app.run(debug=True)
