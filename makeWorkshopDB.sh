#!/bin/bash
rm -f workshops.db
sqlite3 workshops.db <<EOF
create table workshops(workshop TEXT);
.import workshops.csv workshops
EOF
