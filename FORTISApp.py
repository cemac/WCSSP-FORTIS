import os
import sys
from flask import Flask, render_template, flash, redirect, url_for, request
from flask import g, session, abort, send_from_directory
from wtforms import Form, validators, StringField, TextAreaField
from wtforms import SelectField, PasswordField
from werkzeug.utils import secure_filename
from passlib.hash import sha256_crypt
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from random import randint
import boto3
import json
import mammoth
import pandas as pd
app = Flask(__name__)

# GoogleDrive authentication
gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)

# Set config variables:
assert "APP_SETTINGS" in os.environ, "APP_SETTINGS environment variable not set"
assert "SECRET_KEY" in os.environ, "SECRET_KEY environment variable not set"
assert "ADMIN_PWD" in os.environ, "ADMIN_PWD environment variable not set"
assert "DATABASE_URL" in os.environ, "DATABASE_URL environment variable not set"
app.config.from_object(os.environ['APP_SETTINGS'])

# Configure postgresql database:
db = SQLAlchemy(app)
from models import Trainees, Trainers, Workshops, Files, Timetables, Folders
# ######### GLOBAL VARIABLES ##########
typeDict = {
    'lectures1': 'Day 1 / Lectures / ',
    'practicals1': 'Day 1 / Practical 1 /',
    'practicals2-1': 'Day 1 / Practical 2 / ',
    'lectures2': 'Day 2 / Lectures / ',
    'practicals2': 'Day 2 / Practical 1 / ',
    'practicals2-2': 'Day 2 / Practical 2 / ',
    'lectures3': 'Day 3 / Lectures / ',
    'practicals3': 'Day 3 / Practical 1 / ',
    'practicals2-3': 'Day 3 / Practical 2 / ',
    'lectures4': 'Day 4 / Lectures / ',
    'practicals4': 'Day 4 / Practical 1 / ',
    'practicals2-4': 'Day 4 / Practical 2 / ',
    'lectures5': 'Day 5 / Lectures / ',
    'practicals5': 'Day 5 / Practical 1 / ',
    'other': 'Other'
}
######################################

# ######### PSQL FUNCTIONS ##########


def psql_to_pandas(query):
    df = pd.read_sql(query.statement, db.session.bind)
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


# ######### LOGGED-IN FUNCTIONS ##########
# Check if user is logged in


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorised, please login', 'danger')
            return redirect(url_for('index'))
    return wrap

# Check if user is logged in as a trainer/admin


def is_logged_in_as_trainer(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session and (session['usertype'] == 'trainer' or session['usertype'] == 'admin'):
            return f(*args, **kwargs)
        else:
            flash('Unauthorised, please login as a trainer/admin', 'danger')
            return redirect(url_for('index'))
    return wrap

# Check if user is logged in as admin


def is_logged_in_as_admin(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session and session['usertype'] == 'admin':
            return f(*args, **kwargs)
        else:
            flash('Unauthorised, please login as admin', 'danger')
            return redirect(url_for('index'))
    return wrap
#########################################

########## MISC FUNCTIONS ##########
# Get list of workshops from workshop DB:


def get_workshop_list():
    workshopDF = psql_to_pandas(Workshops.query)
    workshopList = [('blank', '--Please select--')]
    for w in workshopDF['workshop']:
        workshopList.append((w, w))
    return workshopList

# Get list of types for Upload Form:


def get_type_list(workshop):
    typeList = [('blank', '--Please select--')]
    # Add default folders:
    for key, value in typeDict.items():
        typeList.append((key, value))
    # Add custom folders:
    foldersDF = psql_to_pandas(Folders.query.filter_by(workshop=workshop))
    for index, row in foldersDF.iterrows():
        key = row['parent'] + '_' + row['name']
        value = typeDict[row['parent']] + row['name']
        typeList.append((key, value))
    # Sort by second element:
    typeList = sorted(typeList, key=lambda tup: tup[1])
    return typeList
####################################

# ######### FORM CLASSES ##########


class TimetableForm(Form):
    workshop = SelectField(u'Select the workshop that this timetable is for',
                           [validators.NoneOf(('blank'), message='Please select')])


class UploadForm(Form):
    title = StringField(u'Title of material', [
                        validators.required(), validators.Length(min=1, max=50)])
    description = TextAreaField(u'Description of material', [
                                validators.optional(), validators.Length(max=1000)])
    type = SelectField('Select the type of material you are uploading',
                       [validators.NoneOf(('blank'), message='Please select')])
    who = SelectField('Is the material for trainees (typically non-editable files, e.g. PDFs) or trainers (typically editable files, e.g. PPTs)',
                      [validators.NoneOf(('blank'), message='Please select')],
                      choices=[('blank', '--Please select--'),
                               ('trainees', 'Trainees'),
                               ('trainers', 'Trainers')])


class RegisterForm(Form):
    username = StringField('Username',
                           [validators.Regexp('^BMKG_participant-[0-9]{2}$',
                                              message='Username must be of the form BMKG_participant-XX where XX is a two-digit number')])
    password = PasswordField('Password',
                             [validators.Regexp('^([a-zA-Z0-9]{8,})$',
                                                message='Password must be mimimum 8 characters and contain only uppercase letters, \
        lowercase letters and numbers')])


class RegisterTrainerForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=25)])
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

# ####################################
# ######### START OF ROUTES ##########
# ####################################

# Index


@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == 'POST':
        # Get form fields
        username = request.form['username']
        password_candidate = request.form['password']
        # Check trainee accounts first:
        user = Trainees.query.filter_by(username=username).first()
        if user is not None:
            password = user.password
            # Compare passwords
            if password_candidate == password:
                # Passed
                session['logged_in'] = True
                session['username'] = username
                session['usertype'] = 'trainee'
                flash('You are now logged in', 'success')
                return redirect(url_for('index'))
            else:
                flash('Incorrect password', 'danger')
                return redirect(url_for('index'))
        # Check trainer accounts next:
        user = Trainers.query.filter_by(username=username).first()
        if user is not None:
            password = user.password
            # Compare passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username
                if username != 'sam_hardy':
                    session['usertype'] = 'trainer'
                    flash('You are now logged in', 'success')
                elif username == 'sam_hardy':
                    session['usertype'] = 'admin'
                    flash('You are now logged in with admin privillages', 'success')
                return redirect(url_for('index'))
            else:
                flash('Incorrect password', 'danger')
                return redirect(url_for('index'))
        # Finally check admin account:
        if username == 'admin':
            password = app.config['ADMIN_PWD']
            if password_candidate == password:
                # Passed
                session['logged_in'] = True
                session['username'] = 'admin'
                session['usertype'] = 'admin'
                flash('You are now logged in', 'success')
                return redirect(url_for('index'))
            else:
                flash('Incorrect password', 'danger')
                return redirect(url_for('index'))
        # Username not found:
        flash('Username not found', 'danger')
        return redirect(url_for('index'))
    return render_template('home.html.j2')


@app.route('/about')
def about():
    return render_template('about.html.j2')


@app.route('/timetables', methods=["GET", "POST"])
@is_logged_in
def timetables():
    form = TimetableForm(request.form)
    form.workshop.choices = get_workshop_list()
    timetablesData = psql_to_pandas(Timetables.query)
    # If user tries to upload a timetable
    if request.method == 'POST':
        if form.validate():
            # dropbox
            file = request.files['file']
            filename = str(randint(10000, 99999)) + '_' + \
                    secure_filename(file.filename)
            # Get fields from web-form
            workshop = form.workshop.data
            author = session['username']
            # Delete old timetable if it exists:
            timetable = Timetables.query.filter_by(workshop=workshop).first()
            if timetable is not None:
                old_filename = timetable.filename
                # Delete from DB:
                psql_delete(timetable)
                # Delete from cloud:
                try:
                    #dropbox
                    delete_file_from_dbx(old_filename)
                except:
                    flash("Unable to delete timetable from cloud", "warning")
            # Insert new timetable into database:
            db_row = Timetables(filename=filename,
                                workshop=workshop, author=author)
            id = psql_insert(db_row)
            # dropbox
            upload_file_to_dbx(file, filename)
            # flash success message and reload page
            flash('Timetable uploaded successfully', 'success')
            return redirect(url_for('timetables'))
        else:
            # Flash error message:
            flash('Fix form errors and try again', 'danger')
    return render_template('timetables.html.j2', form=form, timetablesData=timetablesData)


@app.route('/partners')
def partners():
    return render_template('partners.html.j2')


@app.route('/contact-us')
def contact_us():
    return render_template('contact-us.html.j2')


@app.route('/select-workshop/<string:linkTo>')
@is_logged_in
def select_workshop(linkTo):
    workshopsData = psql_to_pandas(Workshops.query)
    return render_template('select-workshop.html.j2', workshopsData=workshopsData, linkTo=linkTo)


@app.route('/training-material/<string:workshopID>')
@is_logged_in
def training_material(workshopID):
    # Check workshop exists:
    result = Workshops.query.filter_by(id=workshopID).first()
    if result is None:
        abort(404)
    workshop = result.workshop
    # Subset Files and Folders data:
    allFilesData = psql_to_pandas(Files.query)
    filesData = allFilesData.loc[allFilesData['workshop'] == workshop]
    allfoldersData = psql_to_pandas(Folders.query)
    foldersData = allfoldersData.loc[allfoldersData['workshop'] == workshop]
    return render_template('material.html.j2', filesData=filesData, foldersData=foldersData,
                           workshop=workshop, who='trainees')


@app.route('/trainer-material/<string:workshopID>')
@is_logged_in_as_trainer
def trainer_material(workshopID):
    # Check workshop exists:
    result = Workshops.query.filter_by(id=workshopID).first()
    if result is None:
        abort(404)
    workshop = result.workshop
    # Subset Files and Folders data:
    allFilesData = psql_to_pandas(Files.query)
    filesData = allFilesData.loc[allFilesData['workshop'] == workshop]
    allfoldersData = psql_to_pandas(Folders.query)
    foldersData = allfoldersData.loc[allfoldersData['workshop'] == workshop]
    return render_template('material.html.j2', filesData=filesData, foldersData=foldersData,
                           workshop=workshop, who='trainers')


@app.route('/upload/<string:workshopID>', methods=["GET", "POST"])
@is_logged_in_as_trainer
def upload(workshopID):
    # Check workshop exists:
    result = Workshops.query.filter_by(id=workshopID).first()
    if result is None:
        abort(404)
    workshop = result.workshop
    # Prepare form:
    form = UploadForm(request.form)
    form.type.choices = get_type_list(workshop)
    # If user tries to upload a file
    if request.method == 'POST':
        if form.validate():
            # dropbox
            file = request.files['file']
            filename = (str(randint(10000, 99999)) + '_' +
                        secure_filename(file.filename))
            # Get fields from web-form
            title = form.title.data
            description = form.description.data
            type = form.type.data
            who = form.who.data
            author = session['username']
            # Insert into files database:
            db_row = Files(filename=filename, title=title, description=description,
                           workshop=workshop, type=type, who=who, author=author)
            id = psql_insert(db_row)
            # Save file to dropbox
            upload_file_to_dbx(file, filename)
            # flash success message and reload page
            flash('File uploaded successfully', 'success')
            return redirect(url_for('upload', workshopID=workshopID))
        else:
            # Flash error message:
            flash('Fix form errors and try again', 'danger')
    # If user just navigates to page
    return render_template('upload.html.j2', form=form, workshop=workshop,
                           workshopID=workshopID)


@app.route('/trainee-accounts', methods=["GET", "POST"])
@is_logged_in_as_trainer
def trainee_accounts():
    usersData = psql_to_pandas(Trainees.query.order_by(Trainees.username))
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        # Check username is unique
        user = Trainees.query.filter_by(username=username).first()
        if user is not None:
            flash('Username already exists', 'danger')
            return redirect(url_for('trainee_accounts'))
        password = form.password.data
        db_row = Trainees(username=username, password=password)
        id = psql_insert(db_row)
        flash('Trainee account added', 'success')
        return redirect(url_for('trainee_accounts'))
    return render_template('trainee-accounts.html.j2', form=form, usersData=usersData)


@app.route('/trainer-accounts', methods=["GET", "POST"])
@is_logged_in_as_admin
def trainer_accounts():
    usersData = psql_to_pandas(Trainers.query)
    form = RegisterTrainerForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        # Check username is unique
        user = Trainers.query.filter_by(username=username).first()
        if user is not None:
            flash('Username already exists', 'danger')
            return redirect(url_for('trainer_accounts'))
        if username == 'admin' or username.startswith('trainee'):
            flash('Username not allowed', 'danger')
            return redirect(url_for('trainer_accounts'))
        password = sha256_crypt.encrypt(str(form.password.data))
        db_row = Trainers(username=username, password=password)
        id = psql_insert(db_row)
        flash('Trainer account added', 'success')
        return redirect(url_for('trainer_accounts'))
    return render_template('trainer-accounts.html.j2', form=form, usersData=usersData)


@app.route('/change-pwd', methods=["GET", "POST"])
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
            return redirect(url_for('change_pwd'))
        else:
            flash('Current password incorrect', 'danger')
            return redirect(url_for('change_pwd'))
    return render_template('change-pwd.html.j2', form=form)


@app.route('/workshops', methods=["GET", "POST"])
@is_logged_in_as_admin
def workshops():
    workshopsData = psql_to_pandas(Workshops.query)
    if request.method == 'POST':
        workshop = request.form['workshop']
        db_row = Workshops(workshop=workshop)
        id = psql_insert(db_row)
        flash('Workshop added', 'success')
        return redirect(url_for('workshops'))
    return render_template('workshops.html.j2', workshopsData=workshopsData)


@app.route('/folders/<string:id>')
@is_logged_in_as_admin
def folders(id):
    # Retrieve workshop:
    result = Workshops.query.filter_by(id=id).first()
    if result is None:
        abort(404)
    allFoldersData = psql_to_pandas(Folders.query)
    foldersData = allFoldersData.loc[allFoldersData['workshop']
                                     == result.workshop]
    return render_template('folders.html.j2', data=foldersData, workshopName=result.workshop, workshopID=id)


@app.route('/add-folder/<string:id>/<string:parent>', methods=["POST"])
@is_logged_in_as_admin
def add_folder(id, parent):
    # Retrieve workshop:
    workshop = Workshops.query.filter_by(id=id).first().workshop
    name = request.form['folder']
    db_row = Folders(workshop=workshop, parent=parent, name=name)
    dummy = psql_insert(db_row)
    return redirect(url_for('folders', id=id))


@app.route('/delete-folder/<string:id>', methods=["POST"])
@is_logged_in_as_admin
def delete_folder(id):
    # Retrieve folder:
    folder = Folders.query.filter_by(id=id).first()
    if folder is None:
        abort(404)
    # Retrieve workshop id:
    workshop = folder.workshop
    workshopID = Workshops.query.filter_by(workshop=workshop).first().id
    # Check folder is empty:
    type = folder.parent + '_' + folder.name
    filesInFolder = Files.query.filter_by(workshop=workshop, type=type).first()
    if filesInFolder is not None:
        flash("Cannot delete folder until it is empty (check both trainee and trainer material)", "danger")
        return redirect(url_for('folders', id=workshopID))
    # Delete from DB:
    psql_delete(folder)
    flash("Folder deleted", "success")
    return redirect(url_for('folders', id=workshopID))


@app.route('/edit/<string:id>', methods=["POST"])
@is_logged_in_as_trainer
def edit(id):
    result = Files.query.filter_by(id=id).first()
    if result is None:
        abort(404)
    workshop = result.workshop
    if 'edit' in request.form:
        form = UploadForm()
        form.type.choices = get_type_list(workshop)
        form.title.data = result.title
        form.description.data = result.description
        form.type.data = result.type
        form.who.data = result.who
        return render_template('edit.html.j2', form=form, id=id)
    else:
        form = UploadForm(request.form)
        form.type.choices = get_type_list(workshop)
        if form.validate():
            if 'file' in request.files:
                file = request.files['file']
                filename = str(randint(10000, 99999)) + \
                    '_' + secure_filename(file.filename)
            else:
                filename = ''
            # Delete old file if not blank:
            if not filename == '':
                old_filename = result.filename
                # dropbox
                delete_file_from_dbx(old_filename)
                # Save new file to dropbox:
                upload_file_to_dbx(file, filename)
                result.filename = filename
            # Get form info:
            title = form.title.data
            description = form.description.data
            type = form.type.data
            who = form.who.data
            # Update DB:
            result.title = title
            result.description = description
            result.type = type
            result.who = who
            db.session.commit()
            flash('File edits successful', 'success')
            return redirect(url_for('index'))
        else:
            # Flash error message:
            flash('Invalid option selected, please try to edit the file again', 'danger')
            return redirect(url_for('index'))

# Download file (Dropbox only)


@app.route('/download-file/<string:id>', methods=['POST'])
@is_logged_in
def download_file(id):
    result = Files.query.filter_by(id=id).first()
    if result is None:
        abort(404)
    filename = result.filename
    # Try to download the file from dbx to /tmp if it's not already there:
    if not os.path.exists('/tmp/' + filename):
        try:
            download_file_from_dbx(filename)
        except:
            flash("Unable to download file", "danger")
            return redirect(url_for('index'))
    # Serve the file to the client:
    if os.path.exists('/tmp/' + filename):
        return send_from_directory('/tmp', filename, as_attachment=True, attachment_filename=filename)
    else:
        abort(404)

# Download timetable (Dropbox only)


@app.route('/download-timetable/<string:id>', methods=['POST'])
@is_logged_in
def download_timetable(id):
    result = Timetables.query.filter_by(id=id).first()
    if result is None:
        abort(404)
    filename = result.filename
    # Try to download the timetable from dbx to /tmp if it's not already there:
    if not os.path.exists('/tmp/' + filename):
        try:
            download_file_from_dbx(filename)
        except:
            flash("Unable to download timetable", "danger")
            return redirect(url_for('timetables'))
    # Serve the timetable to the client:
    if os.path.exists('/tmp/' + filename):
        return send_from_directory('/tmp', filename, as_attachment=True, attachment_filename=filename)
    else:
        abort(404)

# View timetable (Dropbox only; docx files only)


@app.route('/view-timetable/<string:id>')
@is_logged_in
def view_timetable(id):
    #dropbox
    result = Timetables.query.filter_by(id=id).first()
    if result is None:
        abort(404)
    filename = result.filename
    # Try to download the timetable from dbx to /tmp if it's not already there:
    if not os.path.exists('/tmp/' + filename):
        try:
            download_file_from_dbx(filename)
        except:
            flash("Unable to download timetable", "danger")
            return redirect(url_for('timetables'))
    # Convert to HTML:
    try:
        with open('/tmp/' + filename, "rb") as docx_file:
            result = mammoth.convert_to_html(docx_file)
            text = result.value
            print(text)
            return text
    except:
        flash("Unable to convert to html", "danger")
        return redirect(url_for('timetables'))

# Delete file


@app.route('/delete-file/<string:id>', methods=['POST'])
@is_logged_in_as_trainer
def delete_file(id):
    result = Files.query.filter_by(id=id).first()
    if result is None:
        abort(404)
    filename = result.filename
    # Delete from DB:
    psql_delete(result)
    # Delete from cloud:
    try:
        #dropbox
        delete_file_from_dbx(filename)
    except:
        flash("Unable to delete file from cloud", "warning")
    flash("File deleted", "success")
    return redirect(url_for('index'))

# Delete timetable


@app.route('/delete-timetable/<string:id>', methods=['POST'])
@is_logged_in_as_trainer
def delete_timetable(id):
    result = Timetables.query.filter_by(id=id).first()
    if result is None:
        abort(404)
    filename = result.filename
    # Delete from DB:
    psql_delete(result)
    # Delete from cloud:
    try:
        # dropbox
        delete_file_from_dbx(filename)
    except:
        flash("Unable to delete timetable from cloud", "warning")
    flash("Timetable deleted", "success")
    return redirect(url_for('timetables'))

# Delete trainee


@app.route('/delete-trainee/<string:id>', methods=['POST'])
@is_logged_in_as_admin
def delete_trainee(id):
    result = Trainees.query.filter_by(id=id).first()
    if result is None:
        abort(404)
    psql_delete(result)
    flash('Trainee account deleted', 'success')
    return redirect(url_for('trainee_accounts'))

# Delete trainer


@app.route('/delete-trainer/<string:id>', methods=['POST'])
@is_logged_in_as_admin
def delete_trainer(id):
    result = Trainers.query.filter_by(id=id).first()
    if result is None:
        abort(404)
    psql_delete(result)
    flash('Trainer account deleted', 'success')
    return redirect(url_for('trainer_accounts'))

# Delete workshop


@app.route('/delete-workshop/<string:id>', methods=['POST'])
@is_logged_in_as_admin
def delete_workshop(id):
    result = Workshops.query.filter_by(id=id).first()
    if result is None:
        abort(404)
    psql_delete(result)
    flash('Workshop deleted', 'success')
    return redirect(url_for('workshops'))

# Logout


@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
