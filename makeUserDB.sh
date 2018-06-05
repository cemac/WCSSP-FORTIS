#!/bin/bash
rm -f users.db
sqlite3 users.db <<EOF
create table users(usertype TEXT, username TEXT, password TEXT);
.separator ","
.import users.csv users
EOF
