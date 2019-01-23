#######################################################################################

Package Requirements: Ansible, Libvirt, Python, Shell, sshpass, docker, .

A custom template.img was used to deploy VMs and similarly another template.img was used to deploy Controller VM. This scripts assume that these image files are located at /var/lib/libvirt/images/ directory. Also another docker image was created on top bae Ubuntu docker image with packages: iproute2,ping,isc-dhcp-server,openssh2,tcpdump and this image was used to deploy Containers.

Operating System tested on: Ubuntu 16.04.5 LTS

These scripts assume ssh keys are configured between the Hypervisors.

Required files: All files provided in the scripts directory. Schema.json can be modified.

Usage: cd into the scripts directory and run this command with the JSON Input File:

./main.sh

Creates the complete infrastructure for the Tenant including the Controller VMs.
Controller.py - This script has the core logic built inside and needs to be scheduled using start_controller.py (Default 5 Min Cron job). Usage: python controller.py - takes no argument. This file assumes schema.json and mgmtdetails.json files are present.

Directory Structure: Onboarding: Contains scripts for initial setup till the Controller takes over. autoscaler: Controller resides in this directory and this will be run from Controller VM. Note that there are two versions of autoscaler - One for Containers and One for VMs.

To use Containers: copy Container/autoscaler and onboarding directories in the same directory in the main hypervisor. Make sure to AVOID copying any files from VM directory. Populate mgmtdetails in onboarding directory with available Hypervisor list. Create/take the schema.json. Run Main.sh with schema.json

To use VM: copy VM/autoscaler and onboarding directories in the same directory. Make sure to AVOID copying any files from Container directory. Populate mgmtdetails in onboarding directory with available Hypervisor list. Create/take the schema.json. Run Main.sh with schema.json

#######################################################################################

