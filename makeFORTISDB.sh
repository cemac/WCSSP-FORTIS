#!/bin/bash

if [ ! -f ./FORTIS.db ]; then

sqlite3 FORTIS.db <<EOF
create table trainees(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT);
create table trainers(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT);
create table workshops(id INTEGER PRIMARY KEY AUTOINCREMENT, workshop TEXT);
create table files(id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, title TEXT, description TEXT, workshop TEXT, type TEXT, who TEXT);
create table timetables(id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, workshop TEXT);
EOF

fi
