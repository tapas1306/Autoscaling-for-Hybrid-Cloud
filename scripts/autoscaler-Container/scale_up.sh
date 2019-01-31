#!/bin/bash

user="root"
password="kushaltapas"
hypervisorip=$1
hypervisoruser=$2
con_name=$3
net_name=$4
mgmt_net_name=$5
controllerip=$6
nsname=$7
num_con=$8
vethIP=$9
mgmthypip=${10}
mgmthypuser=${11}
con_image_name=${12}
br_name=${13}
updatejson=${14}
updateLB=${15}
host_file_name="inventory"

#-------------------Create Container--------------------

ssh $hypervisoruser@$hypervisorip docker run -itd --name $con_name $con_image_name
con_pid=`ssh $hypervisoruser@$hypervisorip docker inspect -f '{{.State.Pid}}' $con_name`

#------------------Create Veth Pair---------------------

#------------------Connect to Mgmt Bridge---------------

br_postfix="br"
hifen='-'

bridge_name="${mgmt_net_name}$hifen${br_postfix}"
con_br="${con_name}$hifen${mgmt_net_name}"
br_con="${mgmt_net_name}$hifen${con_name}"

ssh $hypervisoruser@$hypervisorip ip link add name $con_br type veth peer name $br_con
ssh $hypervisoruser@$hypervisorip ip link set dev $con_br netns $con_pid
ssh $hypervisoruser@$hypervisorip brctl addif $bridge_name $br_con
ssh $hypervisoruser@$hypervisorip docker exec --privileged $con_name ip link set $con_br up
ssh $hypervisoruser@$hypervisorip ip link set $br_con up

ssh $hypervisoruser@$hypervisorip docker exec --privileged $con_name dhclient $con_br

#-------------------Find mgmt IP-----------------

str=`ssh $hypervisoruser@$hypervisorip docker exec --privileged $con_name ip addr show $con_br | grep "inet " | awk -F'[: ]+' '{ print $3 }'`

mgmt_ip=${str%/*}
echo "MGMT IP: $mgmt_ip"
#------------------Find mgmt IP Done------------

#------------------Create Veth Pair---------------------

#------------------Connect to Subnet Bridge-------------

bridge_name="${br_name}$hifen${br_postfix}"
con_br="${con_name}$hifen${br_postfix}"
br_con="${br_postfix}$hifen${con_name}"

ssh $hypervisoruser@$hypervisorip ip link add name $con_br type veth peer name $br_con
ssh $hypervisoruser@$hypervisorip ip link set dev $con_br netns $con_pid
ssh $hypervisoruser@$hypervisorip brctl addif $bridge_name $br_con
ssh $hypervisoruser@$hypervisorip docker exec --privileged $con_name ip link set $con_br up
ssh $hypervisoruser@$hypervisorip ip link set $br_con up

echo "Provisioned "
str2=`python getstaticip.py $net_name`
tempArr2=(${str2//;/ })
echo $tempArr2
staticip=${tempArr2[0]}
mask=${tempArr2[1]}
gw=${tempArr2[2]}
echo "ip: $staticip mask: $mask gw: $gw"

ssh $hypervisoruser@$hypervisorip docker exec --privileged $con_name ip addr add $staticip\/$mask dev $con_br

#------------------Update default routes-------

ssh $hypervisoruser@$hypervisorip docker exec --privileged $con_name ip route del default 
ssh $hypervisoruser@$hypervisorip docker exec --privileged $con_name ip route add default via $gw

#------------------Update json------------------
if [ "$updatejson" != "No" ] ; then
echo "Updating json"
python updatejsonadd.py $net_name $hypervisorip $con_name $staticip $mgmt_ip
echo "Updating json done"
else
echo "Not updating json"
fi
#------------------Update json------------------

#----------Update NS for Load Balancing---------
#TBD
if [ "$updateLB" != "No" ] ; then
echo "setting load balancer"
#echo $mgmthypip $mgmthypuser $nsname $staticip $num_vm $vethIP
./LoadBalancer.sh ADD $mgmthypip $mgmthypuser $nsname $staticip $num_con $vethIP
echo "setting load balancer done"
else
echo "not setting load balancer"
fi
#----------Update NS for Load Balancing---------

ts=`date`
log="SCALED_UP"
mkdir -p logs
logcsvname="logs/controller_log.csv"
syslogname="logs/controller_log"
echo "$ts: $mgmthypip: INFO: $log: New resource [$con_name] with IP $staticip and MGMT IP $mgmt_ip available at $hypervisorip" >> $syslogname
if [ ! -f $logcsvname ] ; then
	echo "TIMESTAMP,CONTROLLER IP,ACTION,AFFECTED HYPERVISOR IP,AFFECTED RESOURCE NAME,IP,MANAGEMENT IP" >> $logcsvname
fi
echo "$ts,$controllerip,$log,$hypervisorip,$con_name,$staticip,$mgmt_ip" >> $logcsvname

