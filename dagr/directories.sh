#!/bin/bash
currdir=$1
directories="$(find "${currdir}" -maxdepth 1 -not -path '*/\.*' -type d \( ! -iname ".*" \))"
echo $directories
