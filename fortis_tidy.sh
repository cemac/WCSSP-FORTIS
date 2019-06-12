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
# Usage stated
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
# Unzip function
set_zip() {
  runuzip=true
}
# Take inputs
while getopts 'f:a:o:zh' flag; do
  case "${flag}" in
    f) fname="${OPTARG}" ;;
    a) fortisarchive="${OPTARG}" ;;
    o) outloc="${OPTARG}" ;;
    z) set_zip ;;
    h) print_usage
      exit 1 ;;
    *) print_usage
      exit 1 ;;
  esac
done
# Must specify file name
if [ "$fname" = notset ]; then
  echo "-f <filename> not set"
  echo "-f <filename> is required"
  exit 1
fi
# State settings
echo 'Tidying ' $fname
echo 'from ' $fortisarchive
echo 'to ' $outloc
echo '....'
# Unzip if asked for
if [ "$runuzip" = true ]; then
  echo "unzipping"
  mkdir ${fname:0:(-4)}
  cd ${fname:0:(-4)}
  unzip ../$fname
  cd ..
  fname=${fname:0:(-4)}
fi

echo 'Creating folder structure...'
mkdir ${fname}_tidy
cd ${fname}_tidy
# Loop through days 1-5
# List files transfered
filesT=""
for i in $(seq -f "%01g" 1 5) ;
do
  mkdir Day_$i
  mkdir Day_$i/Practicals
  mkdir Day_$i/Lectures
  echo 'moving files'
  cd ../$fname
  # find files with dayX
  DayXfiles=$(ls | grep -i Day$i)
  # If file naming convention is ignored then try your best to match
  if [ -z "$DayXfiles" ] ;
  then
    DayX1files=$(ls | grep l$i.)
    DayX2files=$(ls | grep -i "_$i.")
    DayX3files=$(ls | grep -i "D$i")
    DayXfiles="$DayX1files $DayX2files $DayX3files"
    echo "Files not formatted with standard file names"
    echo "Trying to work around please verify"
  fi
  # Copy the files over
  echo $DayXfiles 
  cp -p $DayXfiles ../${fname}_tidy/Day_$i/
  filesT="$filesT $DayXfiles"
  cd ../${fname}_tidy/Day_$i
  # remove random number string
  lectures=$(ls | grep -i lect)
  mv $lectures Lectures
  cd Lectures
  fnames=$(ls)
  for line in $fnames ;
  do
    mv $line ${line:6}
  done
  cd ..
  practicals=$(ls | grep -i practical)
  mv $practicals Practicals
  cd Practicals
  fnames=$(ls)
  for line in $fnames ;
  do
    mv $line ${line:6}
  done
  cd ../..
done
echo $filesT
numFT=$(echo $filesT | wc -w)
echo $numFT
numFs=$(ls ../${fname}/* | wc -l)
echo $numFs
if [ ! $numFT == $numFs ] ;
 then
   mkdir Uncategorised
   cd ../${fname}
   missedF=$(ls --ignore=${filesT})
   echo $missedF
   cp -p $missedF ../${fname}_tidy/Uncategorised/
   cd ../${fname}_tidy
fi
echo "checking files ..."
# Check...
badnames=$(find . \! \( -name FORTIS\* \) -type f)
if [ -z "$badnames" ] ;
then
 echo "All files meet convention"
else
 for line in $badnames ;
 do
  numst=$(echo $line | grep -P -o '(?<!\d)\d{5}(?!\d)')
  if [ ! -z $numst ];
  then
    NEW_FILENAME="$(echo $line | sed -e "s|${numst}_||g")";
    mv $line $NEW_FILENAME
    line=$NEW_FILENAME
  fi
  fortmis=$(echo $line | grep "/_")
  if [ ! -z $fortmis ] ;
  then
    NEW_FILENAME="$(echo $line | sed -e "s|/_|/FORTIS_|g")";
    mv $line $NEW_FILENAME
  fi
 done
fi
cd ..
f_orgin=$(find $fname -type f | wc -l)
f_new=$(find ${fname}_tidy -type f | wc -l)
echo $f_orgin " files in " $fname
echo $f_new " files in " ${fname}_tidy
if [ $f_orgin == $f_new ] ;
then
  echo 'Completed folder tidy'
  echo "SAFE to remove " $fname "Do you want to delete" $fname
  read -r -p "Are You Sure? [Y/n] " input
  case $input in
    [yY][eE][sS]|[yY])
      echo "deleting..."
      #rm -rf $fname
      echo "replacing untidy folder with tidy version" ;;
      #mv ${fname}_tidy $fname
    [nN][oO]|[nN])
      echo "Okay keeping untidy folder" ;;
    *)
      echo "Invalid input..."
      echo "Keeping untidy folder" ;;
  esac
else
  echo 'Completed folder tidy'
  echo 'mismatching number of files - Please review non standard file names'
fi
