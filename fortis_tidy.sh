#!/bin/bash -
#title          :fortis_tidy.sh
#description    :Create nice folder dumps from zipped backups
#author         :CEMAC - Helen
#date           :20190607
#version        :1.0
#usage          :./fortis_tidy.sh
#notes          :
#bash_version   :4.2.46(2)-release
#============================================================================

# Defaults
fortisarchive=/nfs/earcemac/projects/fortis/
outloc=$(pwd)
fname=notset
print_usage() {
  echo "
 fortis_tidy.sh
 A CEMAC script to tidy fortis data, from SQL flat format to human readble
 Usage:
  .\fortis_tidy.sh <fname> <opts>
 <fname> folder or file name to tidy
 Options:
  -a tells tider location of achrived file (defaults to cemac space)
  -o tells the tidier where to dump to (defaults to where ever you are)
  -z tells the tidier we're starting from a zip file
  "
}

set_zip() {
  runuzip=true
}
while getopts 'f:a:o:zh' flag; do
  case "${flag}" in
    f) fname="${OPTARG}" ;;
    a) fortisarchive="${OPTARG}" ;;
    o) outloc="${OPTARG}" ;;
    z) set_zip;;
    h) print_usage
      exit 1 ;;
    *) print_usage
      exit 1 ;;
  esac
done

if [ "$fname" = notset ]; then
  echo "-f <filename> not set"
  echo "-f <filename> is required"
  exit 1 ;;
fi

echo 'Tidying ' $fname
echo 'from ' $fortisarchive
echo 'to ' $outloc
echo '....'

if [ "$runuzip" = true ]; then
  echo "unzipping"
  uzip $fname
  # Remove the zip
  fname=${fname:1:(-4)}
fi

echo 'Creating folder structure...'
mkdir ${fname}_tidy
cd ${fname}_tidy
mkdir Day_1
mkdir Day_1/Practicals
mkdir Day_1/Lectures
mkdir Day_2
mkdir Day_2/Practicals
mkdir Day_2/Lectures
mkdir Day_3
mkdir Day_3/Practicals
mkdir Day_3/Lectures
mkdir Day_4
mkdir Day_4/Practicals
mkdir Day_4/Lectures
mkdir Day_5
mkdir Day_5/Practicals
mkdir Day_5/Lectures
