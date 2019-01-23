All the scripts should run on the controller VM. These scripts will be copied to the controller VM once the tenant onboarding is done and Controller is created with other network infrastructure.

start_controller.py ("start" || "stop") 
Usage: start_controller.py start/stop
starts the controller to run in every five minutes.
This scripts sets a cron job to run every 5 min.
triggers controller.py


controller.py: no arguments 
This is the core auto-scaler.
Uses schema.json and mgmtdetails.json
This script uses all the other south-bound scripts.
Some notable scripts are scale_up.sh and scale_down.sh
All other scripts are called internally.
