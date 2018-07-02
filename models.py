from FORTISApp import db

class Trainees(db.Model):
    __tablename__ = 'trainees'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String())
    password = db.Column(db.String())

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return '<id {}>'.format(self.id)

class Trainers(db.Model):
    __tablename__ = 'trainers'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String())
    password = db.Column(db.String())

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return '<id {}>'.format(self.id)

class Workshops(db.Model):
    __tablename__ = 'workshops'

    id = db.Column(db.Integer, primary_key=True)
    workshop = db.Column(db.String())

    def __init__(self, workshop):
        self.workshop = workshop

    def __repr__(self):
        return '<id {}>'.format(self.id)

class Files(db.Model):
    __tablename__ = 'files'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String())
    title = db.Column(db.String())
    description = db.Column(db.String())
    workshop = db.Column(db.String())
    type = db.Column(db.String())
    who = db.Column(db.String())
    author = db.Column(db.String())

    def __init__(self, filename, title, description, workshop, type, who, author):
        self.filename = filename
        self.title = title
        self.description = description
        self.workshop = workshop
        self.type = type
        self.who = who
        self.author = author

    def __repr__(self):
        return '<id {}>'.format(self.id)

class Timetables(db.Model):
    __tablename__ = 'timetables'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String())
    workshop = db.Column(db.String())
    author = db.Column(db.String())

    def __init__(self, filename, workshop, author):
        self.filename = filename
        self.workshop = workshop
        self.author = author

    def __repr__(self):
        return '<id {}>'.format(self.id)
