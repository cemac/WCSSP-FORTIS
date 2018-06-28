#!/bin/bash

if [ -f ./FORTIS.db ]; then

#Extract entries in 'files' table into csv file:
sqlite3 FORTIS.db <<EOF
.mode csv
.out files.csv
select * from files;
EOF
else
touch files.csv
fi


#Make a backup copy of entire database:
mv -f FORTIS.db FORTIS.db.old

#Now create database again and read in csv files:
sqlite3 FORTIS.db <<EOF
create table workshops(workshop TEXT);
.import workshops.csv workshops
.separator ","
create table users(usertype TEXT, username TEXT, password TEXT);
.import users.csv users
create table files(id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, title TEXT, description TEXT, workshop TEXT, type TEXT, who TEXT);
.import files.csv files
EOF

#Delete files.csv:
rm -f files.csv
