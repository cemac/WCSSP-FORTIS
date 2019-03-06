#!/bin/bash
#title          :gen_users.sh
#description    :Generate List of trainee users
#author         :CEMAC - Helen
#date           :20190306
#version        :1.0
#usage          :./gen_users.sh
#notes          :
#bash_version   :4.2.46(2)-release
#============================================================================


number_of_users=42
usernamepat=BMKG_participant-
password_file=~/users.txt
for i in $(seq -f "%02g" 1 30) ;
  do
  username=$usernamepat$i
  userpassword=`apg -n 1`
  echo "UserID:" $username "has been created with the following password " $userpassword >> $password_file
done
