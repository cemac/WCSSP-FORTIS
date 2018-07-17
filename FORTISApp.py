from flask import Flask, render_template, flash, redirect, url_for, request, g, session, abort, send_from_directory
from wtforms import Form, validators, StringField, TextAreaField, SelectField, PasswordField
from werkzeug.utils import secure_filename
from passlib.hash import sha256_crypt
from functools import wraps
import os
import pandas as pd
from flask_sqlalchemy import SQLAlchemy
import boto3
from random import randint
import json

app = Flask(__name__)

#Set config variables:
assert "APP_SETTINGS" in os.environ, "APP_SETTINGS environment variable not set"
assert "SECRET_KEY" in os.environ, "SECRET_KEY environment variable not set"
assert "ADMIN_PWD" in os.environ, "ADMIN_PWD environment variable not set"
assert "DATABASE_URL" in os.environ, "DATABASE_URL environment variable not set"
assert "AWS_ACCESS_KEY_ID" in os.environ, "AWS_ACCESS_KEY_ID environment variable not set"
assert "AWS_SECRET_ACCESS_KEY" in os.environ, "AWS_SECRET_ACCESS_KEY environment variable not set"
assert "S3_BUCKET" in os.environ, "S3_BUCKET environment variable not set"
app.config.from_object(os.environ['APP_SETTINGS'])

#Configure postgresql database:
db = SQLAlchemy(app)
from models import Trainees, Trainers, Workshops, Files, Timetables

#Set subdomain...
#If running locally (or index is the domain) set to blank, i.e. subd=""
#If index is a subdomain, set as appropriate *including* leading slash, e.g. subd="/WCSSP-FORTIS"
#Routes in @app.route() should NOT include subd, but all other references should...
#Use redirect(subd + '/route') rather than redirect(url_for(route))
#Pass subd=subd into every render_template so that it can be used to set the links appropriately
#
subd=""

########## PSQL FUNCTIONS ##########
def psql_to_pandas(query):
    df = pd.read_sql(query.statement,db.session.bind)
    return df

def psql_insert(row):
    db.session.add(row)
    db.session.commit()
    return row.id

def psql_delete(row):
    db.session.delete(row)
    db.session.commit()
    return
####################################

########## S3 FUNCTIONS/ROUTES ##########
def upload_file_to_s3(file, filename):
    #THIS SUBROUTINE SHOULDN'T BE USED NOW - USING DIRECT UPLOAD METHOD INSTEAD
    bucket_name = app.config['S3_BUCKET']
    s3 = boto3.client('s3','eu-west-2')
    s3.upload_fileobj(
        file,
        bucket_name,
        filename,
        ExtraArgs={
            "ACL": "private",
            "ContentType": file.content_type
        }
    )
    return

def download_file_from_s3(filename):
    #THIS SUBROUTINE SHOULDN'T BE USED NOW - USING DIRECT DOWNLOAD METHOD INSTEAD
    bucket_name = app.config['S3_BUCKET']
    s3 = boto3.resource('s3','eu-west-2')
    s3.meta.client.download_file(
        bucket_name,
        filename,
        '/tmp/'+filename
    )
    return

def delete_file_from_s3(filename):
    bucket_name = app.config['S3_BUCKET']
    s3 = boto3.resource('s3','eu-west-2')
    s3.Object(bucket_name,filename).delete()
    return

@app.route('/sign_s3/')
def sign_s3():
    bucket_name = app.config['S3_BUCKET']
    filename_orig = request.args.get('file_name')
    filename_s3 = str(randint(10000,99999)) + '_' + secure_filename(filename_orig)
    file_type = request.args.get('file_type')
    s3 = boto3.client('s3','eu-west-2')
    presigned_post = s3.generate_presigned_post(
      Bucket = bucket_name,
      Key = filename_s3,
      Fields = {"acl": "private", "Content-Type": file_type},
      Conditions = [
        {"acl": "private"},
        {"Content-Type": file_type}
      ],
      ExpiresIn = 3600
    )
    return json.dumps({
      'data': presigned_post,
      'url': 'https://%s.s3.eu-west-2.amazonaws.com/%s' % (bucket_name, filename_s3)
    })

@app.route('/sign_s3_download_timetable/')
def sign_s3_download_timetable():
    bucket_name = app.config['S3_BUCKET']
    id = request.args.get('id')
    # Retrieve s3 filename from DB:
    db_entry = Timetables.query.filter_by(id=id).first()
    filename_s3 = db_entry.filename
    #Access granting:
    if not 'logged_in' in session:
        abort(403)
    # Create and return pre-signed url:
    s3 = boto3.client('s3','eu-west-2')
    presigned_url = s3.generate_presigned_url(
      'get_object',
      Params = {'Bucket': bucket_name, 'Key': filename_s3},
      ExpiresIn = 3600
    )
    return json.dumps({
      'url': presigned_url,
    })

@app.route('/sign_s3_download_file/')
def sign_s3_download_file():
    bucket_name = app.config['S3_BUCKET']
    id = request.args.get('id')
    # Retrieve s3 filename from DB:
    db_entry = Files.query.filter_by(id=id).first()
    filename_s3 = db_entry.filename
    #Access granting:
    who = db_entry.who
    if not 'logged_in' in session:
        abort(403)
    if who=='trainers' and session['usertype']=='trainee':
        abort(403)
    # Create and return pre-signed url:
    s3 = boto3.client('s3','eu-west-2')
    presigned_url = s3.generate_presigned_url(
      'get_object',
      Params = {'Bucket': bucket_name, 'Key': filename_s3},
      ExpiresIn = 3600
    )
    return json.dumps({
      'url': presigned_url,
    })
##################################

########## LOGGED-IN FUNCTIONS ##########
#Check if user is logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorised, please login', 'danger')
            return redirect(subd+'/')
    return wrap

#Check if user is logged in as a trainer/admin
def is_logged_in_as_trainer(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session and (session['usertype']=='trainer' or session['usertype']=='admin'):
            return f(*args, **kwargs)
        else:
            flash('Unauthorised, please login as a trainer/admin', 'danger')
            return redirect(subd+'/')
    return wrap

#Check if user is logged in as admin
def is_logged_in_as_admin(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session and session['usertype']=='admin':
            return f(*args, **kwargs)
        else:
            flash('Unauthorised, please login as admin', 'danger')
            return redirect(subd+'/')
    return wrap
#########################################

########## MISC FUNCTIONS ##########
#Get list of workshops from workshop DB:
def get_workshop_list():
    workshopDF = psql_to_pandas(Workshops.query)
    workshopList=[('blank','--Please select--')]
    for w in workshopDF['workshop']:
        workshopList.append((w,w))
    return workshopList
####################################

########## FORM CLASSES ##########
class TimetableForm(Form):
    workshop = SelectField(u'Select the workshop that this timetable is for',\
        [validators.NoneOf(('blank'),message='Please select')])

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

class RegisterForm(Form):
    username = StringField('Username',
        [validators.Regexp('^trainee-[0-9]{2}$',
        message='Username must be of the form trainee-XX where XX is a two-digit number')])
    password = PasswordField('Password',
        [validators.Regexp('^([a-zA-Z0-9]{8,})$',
        message='Password must be mimimum 8 characters and contain only uppercase letters, \
        lowercase letters and numbers')])

class RegisterTrainerForm(Form):
    username = StringField('Username',[validators.Length(min=4, max=25)])
    password = PasswordField('Password',
        [validators.Regexp('^([a-zA-Z0-9]{8,})$',
        message='Password must be mimimum 8 characters and contain only uppercase letters, \
        lowercase letters and numbers')])

class ChangePwdForm(Form):
    current = PasswordField('Current password',
        [validators.DataRequired()])
    new = PasswordField('New password',
        [validators.Regexp('^([a-zA-Z0-9]{8,})$',
        message='Password must be mimimum 8 characters and contain only uppercase letters, \
        lowercase letters and numbers')])
    confirm = PasswordField('Confirm new password',
        [validators.EqualTo('new', message='Passwords do no match')])
##################################

#####################################
########## START OF ROUTES ##########
#####################################

#Index
@app.route('/', methods=["GET","POST"])
def index():
    if request.method == 'POST':
        #Get form fields
        username = request.form['username']
        password_candidate = request.form['password']
        #Check trainee accounts first:
        user = Trainees.query.filter_by(username=username).first()
        if user is not None:
            password = user.password
            #Compare passwords
            if password_candidate == password:
                #Passed
                session['logged_in'] = True
                session['username'] = username
                session['usertype'] = 'trainee'
                flash('You are now logged in', 'success')
                return redirect(subd+'/')
            else:
                flash('Incorrect password', 'danger')
                return redirect(subd+'/')
        #Check trainer accounts next:
        user = Trainers.query.filter_by(username=username).first()
        if user is not None:
            password = user.password
            #Compare passwords
            if sha256_crypt.verify(password_candidate, password):
                #Passed
                session['logged_in'] = True
                session['username'] = username
                session['usertype'] = 'trainer'
                flash('You are now logged in', 'success')
                return redirect(subd+'/')
            else:
                flash('Incorrect password', 'danger')
                return redirect(subd+'/')
        #Finally check admin account:
        if username == 'admin':
            password = app.config['ADMIN_PWD']
            if password_candidate == password:
                #Passed
                session['logged_in'] = True
                session['username'] = 'admin'
                session['usertype'] = 'admin'
                flash('You are now logged in', 'success')
                return redirect(subd+'/')
            else:
                flash('Incorrect password', 'danger')
                return redirect(subd+'/')
        #Username not found:
        flash('Username not found', 'danger')
        return redirect(subd+'/')
    return render_template('home.html',subd=subd)

@app.route('/about')
def about():
    return render_template('about.html',subd=subd)

@app.route('/timetables', methods=["GET","POST"])
@is_logged_in
def timetables():
    form = TimetableForm(request.form)
    form.workshop.choices = get_workshop_list()
    timetablesData = psql_to_pandas(Timetables.query)
    #If user tries to upload a timetable
    if request.method == 'POST':
        if form.validate():
            #Get S3 filename:
            filename_s3 = request.form['filename_s3']
            #Get fields from web-form
            workshop = form.workshop.data
            author = session['username']
            #Delete old timetable if it exists:
            timetable = Timetables.query.filter_by(workshop=workshop).first()
            if timetable is not None:
                old_filename=timetable.filename
                #Delete from DB:
                psql_delete(timetable)
                #Delete from S3 bucket:
                try:
                    delete_file_from_s3(old_filename)
                except:
                    flash("Unable to delete timetable from S3","warning")
            #Insert new timetable into database:
            db_row = Timetables(filename=filename_s3,workshop=workshop,author=author)
            id = psql_insert(db_row)
            #flash success message and reload page
            flash('Timetable uploaded successfully', 'success')
            return redirect(subd+'/timetables')
        else:
            #Delete file from S3:
            filename_s3 = request.form['filename_s3']
            delete_file_from_s3(filename_s3)
            #Flash error message:
            flash('Fix form errors and try again', 'danger')
    return render_template('timetables.html',subd=subd,form=form,timetablesData=timetablesData)

@app.route('/training-material')
@is_logged_in
def training_material():
    filesData = psql_to_pandas(Files.query)
    workshopDF = psql_to_pandas(Workshops.query)
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
    filesData = psql_to_pandas(Files.query)
    workshopDF = psql_to_pandas(Workshops.query)
    workshopList = workshopDF['workshop'].values.tolist()
    return render_template('material.html',subd=subd,filesData=filesData,workshopList=workshopList,who='trainers')

@app.route('/upload', methods=["GET","POST"])
@is_logged_in_as_trainer
def upload():
    form = UploadForm(request.form)
    form.workshop.choices = get_workshop_list()
    #If user tries to upload a file
    if request.method == 'POST':
        if form.validate():
            #Get S3 filename:
            filename_s3 = request.form['filename_s3']
            #Get fields from web-form
            title = form.title.data
            description = form.description.data
            workshop = form.workshop.data
            type = form.type.data
            who = form.who.data
            author = session['username']
            #Insert into files database:
            db_row=Files(filename=filename_s3,title=title,description=description,workshop=workshop,type=type,who=who,author=author)
            id = psql_insert(db_row)
            #flash success message and reload page
            flash('File uploaded successfully', 'success')
            return redirect(subd+'/upload')
        else:
            #Delete file from S3:
            filename_s3 = request.form['filename_s3']
            delete_file_from_s3(filename_s3)
            #Flash error message:
            flash('Fix form errors and try again', 'danger')
    #If user just navigates to page
    return render_template('upload.html',subd=subd,form=form)

@app.route('/trainee-accounts', methods=["GET","POST"])
@is_logged_in_as_trainer
def trainee_accounts():
    usersData = psql_to_pandas(Trainees.query.order_by(Trainees.username))
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        #Check username is unique
        user = Trainees.query.filter_by(username=username).first()
        if user is not None:
            flash('Username already exists', 'danger')
            return redirect(subd+'/trainee-accounts')
        password = form.password.data
        db_row = Trainees(username=username,password=password)
        id = psql_insert(db_row)
        flash('Trainee account added', 'success')
        return redirect(subd+'/trainee-accounts')
    return render_template('trainee-accounts.html',subd=subd,form=form,usersData=usersData)

@app.route('/trainer-accounts', methods=["GET","POST"])
@is_logged_in_as_admin
def trainer_accounts():
    usersData = psql_to_pandas(Trainers.query)
    form = RegisterTrainerForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        #Check username is unique
        user = Trainers.query.filter_by(username=username).first()
        if user is not None:
            flash('Username already exists', 'danger')
            return redirect(subd+'/trainer-accounts')
        if username == 'admin' or username.startswith('trainee'):
            flash('Username not allowed', 'danger')
            return redirect(subd+'/trainer-accounts')
        password = sha256_crypt.encrypt(str(form.password.data))
        db_row = Trainers(username=username,password=password)
        id = psql_insert(db_row)
        flash('Trainer account added', 'success')
        return redirect(subd+'/trainer-accounts')
    return render_template('trainer-accounts.html',subd=subd,form=form,usersData=usersData)

@app.route('/change-pwd', methods=["GET","POST"])
@is_logged_in_as_trainer
def change_pwd():
    form = ChangePwdForm(request.form)
    if request.method == 'POST' and form.validate():
        user = Trainers.query.filter_by(username=session['username']).first()
        password = user.password
        current = form.current.data
        if sha256_crypt.verify(current, password):
            user.password = sha256_crypt.encrypt(str(form.new.data))
            db.session.commit()
            flash('Password changed', 'success')
            return redirect(subd+'/change-pwd')
        else:
            flash('Current password incorrect', 'danger')
            return redirect(subd+'/change-pwd')
    return render_template('change-pwd.html',subd=subd,form=form)

@app.route('/workshops', methods=["GET","POST"])
@is_logged_in_as_admin
def workshops():
    workshopsData = psql_to_pandas(Workshops.query)
    if request.method == 'POST':
        workshop = request.form['workshop']
        db_row = Workshops(workshop=workshop)
        id = psql_insert(db_row)
        flash('Workshop added', 'success')
        return redirect(subd+'/workshops')
    return render_template('workshops.html',subd=subd,workshopsData=workshopsData)

@app.route('/edit/<string:id>', methods=["POST"])
@is_logged_in_as_trainer
def edit(id):
    result = Files.query.filter_by(id=id).first()
    if result is None:
        abort(404)
    if 'edit' in request.form:
        form = UploadForm()
        form.workshop.choices = get_workshop_list()
        form.title.data = result.title
        form.description.data = result.description
        form.workshop.data = result.workshop
        form.type.data = result.type
        form.who.data = result.who
        return render_template('edit.html',subd=subd,form=form,id=id)
    else:
        form = UploadForm(request.form)
        form.workshop.choices = get_workshop_list()
        if form.validate():
            #Get S3 filename and delete old file if not blank:
            filename_s3 = request.form['filename_s3']
            if not filename_s3 == "":
                old_filename=result.filename
                delete_file_from_s3(old_filename)
                result.filename = filename_s3
            #Get form info:
            title = form.title.data
            description = form.description.data
            workshop = form.workshop.data
            type = form.type.data
            who = form.who.data
            #Update DB:
            result.title = title
            result.description = description
            result.workshop = workshop
            result.type = type
            result.who = who
            db.session.commit()
            flash('File edits successful', 'success')
            return redirect(subd+'/')
        else:
            #Delete file from S3 if not blank:
            filename_s3 = request.form['filename_s3']
            if not filename_s3 == "":
                delete_file_from_s3(filename_s3)
            #Flash error message:
            flash('Invalid option selected, please try to edit the file again', 'danger')
            return redirect(subd+'/')

#Download file
@app.route('/download-file/<string:id>', methods=['POST'])
#THIS ROUTE SHOULDN'T BE USED NOW - USING DIRECT DOWNLOAD METHOD INSTEAD
@is_logged_in
def download_file(id):
    result = Files.query.filter_by(id=id).first()
    if result is None:
        abort(404)
    filename = result.filename
    #Try to download the file from S3 bucket to /tmp if it's not already there:
    if not os.path.exists('/tmp/'+filename):
        try:
            download_file_from_s3(filename)
        except:
            flash("Unable to download file","danger")
            return redirect(subd+'/timetables')
    #Serve the file to the client:
    if os.path.exists('/tmp/'+filename):
        return send_from_directory('/tmp',filename,as_attachment=True,attachment_filename=filename)
    else:
        abort(404)

#Download timetable
@app.route('/download-timetable/<string:id>', methods=['POST'])
#THIS ROUTE SHOULDN'T BE USED NOW - USING DIRECT DOWNLOAD METHOD INSTEAD
@is_logged_in
def download_timetable(id):
    result = Timetables.query.filter_by(id=id).first()
    if result is None:
        abort(404)
    filename = result.filename
    #Try to download the timetable from S3 bucket to /tmp if it's not already there:
    if not os.path.exists('/tmp/'+filename):
        try:
            download_file_from_s3(filename)
        except:
            flash("Unable to download timetable","danger")
            return redirect(subd+'/timetables')
    #Serve the timetable to the client:
    if os.path.exists('/tmp/'+filename):
        return send_from_directory('/tmp',filename,as_attachment=True,attachment_filename=filename)
    else:
        abort(404)

#Delete file
@app.route('/delete-file/<string:id>', methods=['POST'])
@is_logged_in_as_trainer
def delete_file(id):
    result = Files.query.filter_by(id=id).first()
    if result is None:
        abort(404)
    filename = result.filename
    #Delete from DB:
    psql_delete(result)
    #Delete from S3 bucket:
    try:
        delete_file_from_s3(filename)
    except:
        flash("Unable to delete file from S3","warning")
    flash("File deleted","success")
    return redirect(subd+'/')

#Delete timetable
@app.route('/delete-timetable/<string:id>', methods=['POST'])
@is_logged_in_as_trainer
def delete_timetable(id):
    result = Timetables.query.filter_by(id=id).first()
    if result is None:
        abort(404)
    filename = result.filename
    #Delete from DB:
    psql_delete(result)
    #Delete from S3 bucket:
    try:
        delete_file_from_s3(filename)
    except:
        flash("Unable to delete timetable from S3","warning")
    flash("Timetable deleted","success")
    return redirect(subd+'/timetables')

#Delete trainee
@app.route('/delete-trainee/<string:id>', methods=['POST'])
@is_logged_in_as_admin
def delete_trainee(id):
    result = Trainees.query.filter_by(id=id).first()
    if result is None:
        abort(404)
    psql_delete(result)
    flash('Trainee account deleted', 'success')
    return redirect(subd+'/trainee-accounts')

#Delete trainer
@app.route('/delete-trainer/<string:id>', methods=['POST'])
@is_logged_in_as_admin
def delete_trainer(id):
    result = Trainers.query.filter_by(id=id).first()
    if result is None:
        abort(404)
    psql_delete(result)
    flash('Trainer account deleted', 'success')
    return redirect(subd+'/trainer-accounts')

#Delete workshop
@app.route('/delete-workshop/<string:id>', methods=['POST'])
@is_logged_in_as_admin
def delete_workshop(id):
    result = Workshops.query.filter_by(id=id).first()
    if result is None:
        abort(404)
    psql_delete(result)
    flash('Workshop deleted', 'success')
    return redirect(subd+'/workshops')

#Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(subd+'/')

if __name__ == '__main__':
    app.run(debug=True)
