#!/bin/bash
cleanfilename=$1
size=$2
homedir=$3
find $homedir -type f -size $size -name "$cleanfilename" 2>/dev/null
