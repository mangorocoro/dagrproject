#!/bin/bash
filename=$1
newword=""
loopcounter=1
for word in $filename; do
if [ $loopcounter = 1 ]; then
newword=$word
loopcounter=$(($loopcounter + 1))
else
newword="$newword\ $word"
fi
done
echo $newword
