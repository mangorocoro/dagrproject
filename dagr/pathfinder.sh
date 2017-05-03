#!/bin/bash
filename=$1
size-$2
homedir=$3
find $3 -type f -size $2 -name $filename 2>/dev/null
