#!/bin/bash

pushd . > /dev/null

BASEDIR=$(dirname "$0")

oldport=19997          
gnome-terminal -- bash -c "cd ${BASEDIR}/CoppeliaSim_Edu_V4_0_0_Ubuntu18_04/ ; ./coppeliaSim.sh"
sleep 5 
for i in {1..3};do
	newport=$((19997 - i)) 	
	sed -i.bak "s/$oldport/$newport/" $BASEDIR/CoppeliaSim_Edu_V4_0_0_Ubuntu18_04/remoteApiConnections.txt 	
	gnome-terminal -- bash -c "cd ${BASEDIR}/CoppeliaSim_Edu_V4_0_0_Ubuntu18_04/ ; ./coppeliaSim.sh -h" 
	sleep 5
	oldport=$newport
done

sed -i.bak "s/$oldport/19997/" $BASEDIR/CoppeliaSim_Edu_V4_0_0_Ubuntu18_04/remoteApiConnections.txt

popd >/dev/null
