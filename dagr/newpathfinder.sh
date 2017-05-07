#!/bin/bash
numargs=$#
concatrange=$(($numargs - 2))
count=2
newname=$1
for i in ${@:2}; do
if [ "$count" -le "$concatrange" ]; then
newname="$newname\ ${i}"
count=$(($count+1))
fi
done
size=${@: -2:1}
homedir=${@: -1:1}
find $homedir -type f -size $size -name $newname 2>/dev/null
