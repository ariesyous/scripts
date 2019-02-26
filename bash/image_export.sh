#!/bin/bash
# Author: Aries Youssefian
# 
# This script takes an image ID, converts it to a snapshot, attaches it to the host, converts it to a qcow2 on mancala0 on the host it's ran from.  
# 
# Must be run from a Symphony node. 
# SCRIPT ASSUMES SOURCE NODE HAS ENOUGH SPACE ON mancala0
# Script also assumes only 1 project exists per source and destination domain (eg, default)
# if more projects exist, specify -r flag for the project 
#
# Tested on Symphony 4.2.7.4
#
# Todo: Add flags for SSL
#


display_usage() {
	echo "This script takes an image ID, converts it to a snapshot, attaches it to the host, converts it to a qcow2 on mancala0 on the host it's ran from."
	echo -e "\nUsage:\nsource-user-name source-domain source-password source-cluster-address source-image-id \n"
	}

# if less than 5 arguments supplied, display usage
if [  $# -ne 5 ]
then
	display_usage
	exit 1
fi

# check whether user had supplied -h or --help . If yes display usage
if [[ ( $# == "--help") ||  $# == "-h" ]]
then
	display_usage
	exit 0
fi

# Variables 

sourceuser=$1
sourcedomain=$2
sourcepassword=$3
sourcecluster=$4
sourceimageid=$5
sourcehostname="$(hostname)"

echo Getting snapshot of $sourceimageid

sourcesnapid="$(symp -k --url $sourcecluster -d $sourcedomain -u $sourceuser -p $sourcepassword image get-snapshot-from-pool $sourceimageid -f value)"

sourceimagename="$(symp -k --url $sourcecluster -d $sourcedomain -u $sourceuser -p $sourcepassword image get $sourceimageid -f value -c name)"

sourceclonedvolid="$(symp -k --url $sourcecluster -d $sourcedomain -u $sourceuser -p $sourcepassword volume create --source-id $sourcesnapid $sourceimagename -f value -c id)"

echo $sourceimageid has a snapshot ID of $sourcesnapid

echo $sourceimageid has a name of $sourceimagename

echo Cloning successful, cloned volume ID is $sourceclonedvolid

echo Attaching cloned volume $sourceclonedvolid to host $sourcehostname

sourcedevaddress="$(mancala volumes attach-to-host $sourceclonedvolid $sourcehostname --json | jq -r .attachments[].mountpoint)"

echo Successfully mounted cloned volume $sourceclonedvolid to host $sourcehostname at $sourcedevaddress

echo Beginning qemu-img conversion 

qemu-img convert -f raw -O qcow2 -p $sourcedevaddress /mnt/mancala0/$sourceimagename.qcow2

echo Successfully completed conversion to /mnt/mancala0, filename is $sourceimagename.qcow2

echo Unattaching cloned volume $sourceclonevolid from host $sourcehostname

mancala volumes detach-from-host $sourceclonedvolid $sourcehostname

echo Successfully detached cloned volume $sourceclonevolid from host $sourcehostname

echo Deleting cloned volume $sourceclonedvolid 

symp -k --url $sourcecluster -d $sourcedomain -u $sourceuser -p $sourcepassword volume remove $sourceclonedvolid

echo All done. You can find $sourceimagename.qcow2 on /mnt/mancala0 on node $sourcehostname





