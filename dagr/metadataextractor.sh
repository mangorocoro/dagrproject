#!/bin/bash
filename=$1
owner="$(stat -c '%U' "${filename}")"
lastaccess="$(stat -c '%x' "${filename}")"
lastmod="$(stat -c '%y' "${filename}")"
laststatuschange="$(stat -c '%z' "${filename}")"
output=${owner}"^^"${lastaccess}"^^"${lastmod}"^^"${laststatuschange}
echo ${output}
