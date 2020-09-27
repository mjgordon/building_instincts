#!/bin/bash

pushd . > /dev/null

BASEDIR=$(dirname "$0")

default_port=19997
client_count=4

i=0
while [ "$i" -lt "$client_count" ]; do
    newport=$(($default_port - i))
    cmd="cd ${BASEDIR}/CoppeliaSim_Edu_V4_1_0_Ubuntu18_04/ ; ./coppeliaSim.sh -gREMOTEAPISERVERSERVICE_${newport}_FALSE_FALSE"
    if [ "$i" -gt 0 ]
    then
	cmd="${cmd} -h"
    fi
    
    gnome-terminal -- bash -c "$cmd"
    i=$(($i + 1))
done


popd >/dev/null
