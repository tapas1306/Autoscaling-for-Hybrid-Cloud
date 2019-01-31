#!/bin/bash

user="root"
password="kushaltapas"
hypervisorip=$1
hypervisoruser=$2
cont_name=$3
net_name=$4
nsname=$5
num_cont=$6
vethIP=$7
mgmthypip=$8
mgmthypuser=$9
staticip=${10}
updatejson=${11}
updateLB=${12}
host_file_name="inventory"

#------------------Destroy container------------------
echo "Destroying container: $cont_name"
if ! grep -q "$hypervisoruser@$hypervisorip" $host_file_name
then
    # code if not found
    echo -e "[$hypervisoruser@$hypervisorip]\n$hypervisorip\n" >> $host_file_name
fi
echo "Scalep down from $hypervisorip" >> event_log
ansible-playbook -i inventory delete_container.yml -e "host=$hypervisoruser@$hypervisorip cont_name=$cont_name"
#-------------------Destroy container--------------------
#------------------Update json------------------
if [ "$updatejson" != "No" ] ; then
echo "Updating json"
python updatejsondelete.py $net_name $hypervisorip $cont_name
echo "Updating json done"
else
echo "not updating json"
fi
#------------------Update json------------------

#----------Update NS for Load Balancing---------
#TBD
if [ "$updateLB" != "No" ] ; then
echo "Updating LB"
./LoadBalancer.sh REM $mgmthypip $mgmthypuser $nsname $staticip $num_cont $vethIP
echo "Updated LB"
else
echo "Not updating LB"
fi
#----------Update NS for Load Balancing---------

ts=`date`
log="SCALING_DOWN"
mkdir -p logs
logcsvname="logs/controller_log.csv"
syslogname="logs/controller_log"
echo "$ts: $mgmthypip: INFO: $log: Old resource [$con_name] with IP $staticip was removed from $hypervisorip" >> $syslogname
if [ ! -f $logcsvname ] ; then
        echo "TIMESTAMP,CONTROLLER IP,ACTION,AFFECTED HYPERVISOR IP,AFFECTED RESOURCE NAME,IP,MANAGEMENT IP" >> $logcsvname
fi
echo "$ts,$controllerip,$log,$hypervisorip,$con_name,$staticip,$mgmt_ip" >> $logcsvname

