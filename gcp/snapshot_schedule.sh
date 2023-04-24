#!/bin/bash

# Author: Aries Youssefian @ariesyous
#
# This script loops through all instances of a specific project, retrieves the labels
# associated with each instance, and checks if it has either env=prod or env=nonprod as labels.
# It then retrieves the zone, and attaches a snapshot schedule to the disks based their label. As noted
# it will do this for every instance in the project.  
# 


# Replace [YOUR_PROJECT_ID] with your Google Cloud project ID.
PROJECT_ID=[YOUR_PROJECT_ID]

# Loop through all instances in the specified project and get their names and zones.
for instance_info in $(gcloud compute instances list --project $PROJECT_ID --format="csv[no-heading](name,zone)")
do
  # Extract the instance name and zone from the retrieved information.
  IFS=','
  read -ra INSTANCE_DATA <<< "$instance_info"
  instance="${INSTANCE_DATA[0]}"
  ZONE="${INSTANCE_DATA[1]}"

  # Get the labels for the current instance.
  LABELS=$(gcloud compute instances describe $instance --project $PROJECT_ID --zone $ZONE --format="value(labels)")

  # Get the disk name of the instance.
  DISK_NAME=$(gcloud compute instances describe $instance --project $PROJECT_ID --zone $ZONE --format="value(disks[0].deviceName)")

  # Check if the instance has the "env=prod" label.
  if [[ $LABELS == *"env=prod"* ]]; then
    # Attach the "snapshot-schedule-prod" resource policy to the instance's disks.
    gcloud compute disks add-resource-policies $DISK_NAME \
      --project $PROJECT_ID \
      --resource-policies snapshot-schedule-prod \
      --zone $ZONE

  # Check if the instance has the "env=nonprod" label.
  elif [[ $LABELS == *"env=nonprod"* ]]; then
    # Attach the "snapshot-schedule-nonprod" resource policy to the instance's disks.
    gcloud compute disks add-resource-policies $DISK_NAME \
      --project $PROJECT_ID \
      --resource-policies snapshot-schedule-nonprod \
      --zone $ZONE
  fi
done
