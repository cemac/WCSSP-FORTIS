#!/bin/bash

if [ -f ./FORTIS.db ]; then

#Extract entries in 'files' and 'timetables' tables into csv files:
sqlite3 FORTIS.db <<EOF
.mode csv
.out files.csv
select * from files;
.out timtables.csv
select * from timetables;
EOF
#Make a backup copy of entire database:
mv -f FORTIS.db FORTIS.db.old

else

touch files.csv
touch timetables.csv

fi

#Now create database again and read in csv files:
sqlite3 FORTIS.db <<EOF
create table workshops(workshop TEXT);
.import workshops.csv workshops
.separator ","
create table users(usertype TEXT, username TEXT, password TEXT);
.import users.csv users
create table files(id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, title TEXT, description TEXT, workshop TEXT, type TEXT, who TEXT);
.import files.csv files
create table timetables(id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, workshop TEXT);
.import timetables.csv timetables
EOF

#Delete files.csv and timetables.csv:
rm -f files.csv timetables.csv
