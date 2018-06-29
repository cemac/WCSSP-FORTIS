#!/bin/bash

if [ -f ./FORTIS.db ]; then

#Extract existing tables into csv files:
sqlite3 FORTIS.db <<EOF
.mode csv
.out trainees.csv
select * from trainees;
.out trainers.csv
select * from trainers;
.out workshops.csv
select * from workshops;
.out files.csv
select * from files;
.out timetables.csv
select * from timetables;
EOF
#Make a backup copy of entire database:
mv -f FORTIS.db FORTIS.db.old

else

touch trainees.csv trainers.csv workshops.csv files.csv timetables.csv

fi

#Now create database again and read in csv files:
sqlite3 FORTIS.db <<EOF
.separator ","
create table trainees(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT);
.import trainees.csv trainees
create table trainers(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT);
.import trainers.csv trainers
create table workshops(id INTEGER PRIMARY KEY AUTOINCREMENT, workshop TEXT);
.import workshops.csv workshops
create table files(id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, title TEXT, description TEXT, workshop TEXT, type TEXT, who TEXT);
.import files.csv files
create table timetables(id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, workshop TEXT);
.import timetables.csv timetables
EOF

#Delete files.csv and timetables.csv:
rm -f trainees.csv trainers.csv workshops.csv files.csv timetables.csv
