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

# Loop through all instances in the specified project.
for instance in $(gcloud compute instances list --project $PROJECT_ID --format="value(name)")
do
  # Get the labels for the current instance.
  LABELS=$(gcloud compute instances describe $instance --project $PROJECT_ID --format="value(labels)")

  # Check if the instance has the "env=prod" label.
  if [[ $LABELS == *"env=prod"* ]]; then
    # Get the zone of the instance.
    ZONE=$(gcloud compute instances list --project $PROJECT_ID --filter="name=$instance" --format="value(zone)")
    # Attach the "snapshot-schedule-prod" resource policy to the instance's disks.
    gcloud compute disks add-resource-policies $instance \
      --project $PROJECT_ID \
      --resource-policies snapshot-schedule-prod \
      --zone $ZONE

  # Check if the instance has the "env=nonprod" label.
  elif [[ $LABELS == *"env=nonprod"* ]]; then
    # Get the zone of the instance.
    ZONE=$(gcloud compute instances list --project $PROJECT_ID --filter="name=$instance" --format="value(zone)")
    # Attach the "snapshot-schedule-nonprod" resource policy to the instance's disks.
    gcloud compute disks add-resource-policies $instance \
      --project $PROJECT_ID \
      --resource-policies snapshot-schedule-nonprod \
      --zone $ZONE
  fi
done
