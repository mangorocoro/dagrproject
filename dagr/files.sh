#!/bin/bash
currdir=$1
filesonly="$(find ${currdir} -maxdepth 1 -not -path '*/\.*' -type f \( ! -iname ".*" \))"
echo $filesonly
