#!/bin/bash

currentDate=`date`
log="SCALED_UP"
mgmthypip="1.1.1.1"
staticip="2.2.2.2"
mgmt_ip="3.3.3.3"
hypervisorip="4.4.4.4"

echo "$currentDate: $mgmthypip: $log: New resource with IP $staticip and MGMT IP $mgmt_ip available at $hypervisorip" >> log.csv
