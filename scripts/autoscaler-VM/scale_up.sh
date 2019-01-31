#!/bin/bash

user="root"
password="kushaltapas"
hypervisorip=$1
hypervisoruser=$2
vmname=$3
net_name=$4
mgmt_net_name=$5
controllerip=$6
nsname=$7
num_vm=$8
vethIP=$9
mgmthypip=${10}
mgmthypuser=${11}
updatejson=${12}
host_file_name="inventory"

#------------------Create VM------------------
echo "Creating new VM: $vmname"
prefixstr="    \<interface type='network'\>
      \<source network='"
postfixstr="'\/\>
    \<\/interface\>
"
netcmd="${prefixstr}$net_name${postfixstr}"
netcmd+="${prefixstr}$mgmt_net_name${postfixstr}"
mkdir -p XMLs
cp -f vmtemplate.xml XMLs/$vmname.xml
perl -p -i -e "s/\{\{NETWORKPLACEHOLDER\}\}/${netcmd}/g" XMLs/$vmname.xml
sed -i -e "s/{{VMNAME}}/$vmname/g" XMLs/$vmname.xml
imgpath="\/var\/lib\/libvirt\/images\/$vmname.img" 
perl -p -i -e "s/\{\{VMPATH\}\}/$imgpath/g" XMLs/$vmname.xml
#echo "Copying image file"
#scp -o StrictHostKeyChecking=no template.img $hypervisoruser@$hypervisorip:/var/lib/libvirt/images/$vmname.img
#echo "Done copying image file"
if ! grep -q "$hypervisoruser@$hypervisorip" $host_file_name
then
    # code if not found
    echo -e "[$hypervisoruser@$hypervisorip]\n$hypervisorip\n" >> $host_file_name
fi
fullxmlpath=`pwd`/XMLs/$vmname.xml
ansible-playbook -i inventory create_vm.yml -e "host=$hypervisoruser@$hypervisorip vmname=$vmname xmlname=$fullxmlpath"
#-------------------Create VM--------------------
echo "Sleeping for two minutes for the VM to boot"
sleep 120
echo "I'm back up now. Trying 5 times at 30 second interval"
#-------------------Find mgmt IP-----------------
str=`python getmgmtIPandens3MAC.py $hypervisorip $hypervisoruser $vmname`
tempArr=(${str//;/ })
mgmt_ip=${tempArr[0]}
ens3MAC=${tempArr[1]}
echo "MGMT IP: $mgmt_ip"
echo "MAC: $ens3MAC"
#------------------Find mgmt IP Done------------
echo "Sleeping for another minute for ssh services to come up"
sleep 60
echo "I'm back up now. Trying to configure IP"
#------------------Configure Static IP----------
str2=`python getstaticip.py $net_name`
tempArr2=(${str2//;/ })
staticip=${tempArr2[0]}
mask=${tempArr2[1]}
gw=${tempArr2[2]}
#echo "sshpass -p $password ssh -o StrictHostKeyChecking=no $user@$mgmt_ip ip addr add $staticip/$mask dev ens3"
sshpass -p $password ssh -o StrictHostKeyChecking=no $user@$mgmt_ip ip addr add $staticip/$mask dev ens3
sshpass -p $password ssh -o StrictHostKeyChecking=no $user@$mgmt_ip ip route add default via $gw
sshpass -p $password ssh -o StrictHostKeyChecking=no $user@$mgmt_ip ip route show
echo "Configured static IP"
#------------------Configure Static IP----------
#------------------Start Collectd---------------
echo "Setting up collectd"
./start_collectd.sh $vmname $mgmt_ip $controllerip
echo "Setting up collectd done"
#------------------Start Collectd---------------
#------------------Update json------------------
if [ "$updatejson" != "No" ] ; then
echo "Updating json"
python updatejsonadd.py $net_name $hypervisorip $vmname $staticip $mgmt_ip
echo "Updating json done"
else
echo "Not updating json"
fi
#------------------Update json------------------

#----------Update NS for Load Balancing---------
#TBD
echo "setting load balancer"
#echo $mgmthypip $mgmthypuser $nsname $staticip $num_vm $vethIP
./LoadBalancer.sh ADD $mgmthypip $mgmthypuser $nsname $staticip $num_vm $vethIP
echo "setting load balancer"
#----------Update NS for Load Balancing---------
