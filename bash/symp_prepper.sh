#!/bin/bash
# Author: Aries Youssefian
# Purpose: Script will pull the current Xenial Cloud image, make it public
# Also enable Database service and pull the MySQL 5.7 image
# only works on bright sites and default allocations with default credentials
# dbs engine version list --inc -f json for list of engines
# jq '.[] | select(.name == "5.7.00") | .id' for mysql 5.7

display_usage() {
	echo "This script will pull the xenial cloud image, make it public and enable MySQL 5.7 (along with enabling dbaas service)"
	echo -e "\nUsage:\ncluster-ip\n"
	}

# if less than 1 arguments supplied, display usage
if [  $# -lt 1 ]
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

clusterip=$1

echo Pulling Xenial image.

imageid="$(symp -k --url $clusterip -d cloud_admin -u admin -p admin image create --is-public XenialCloud -f value -c id)" 

echo Image created with ID $imageid

echo Uploading Xenial from Ubuntu repo to $imageid

symp -k --url $clusterip -d cloud_admin -u admin -p admin image upload-from-url --no-verify-ssl $imageid https://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-amd64-disk1.img

echo Done uploading xenial image.

echo Fetching MySQL database engine.

engineversion="$(symp -k --url $clusterip -d cloud_admin -u admin -p admin dbs engine version list --inc -f json | jq -r '.[] | select(.name == "5.7.00") | .id')"

echo Engine version of MySQL 5.7 is $engineversion

echo Enabling the MySQL 5.7 engine.

symp -k --url $clusterip -d cloud_admin -u admin -p admin dbs engine version update $engineversion --enable True

echo Done enabling MySQL 5.7 engine.


