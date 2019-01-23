#!/bin/bash

user="root"
password="kushaltapas"
hypervisorip=$1
hypervisoruser=$2
vmname=$3
net_name=$4
nsname=$5
num_vm=$6
vethIP=$7
mgmthypip=$8
mgmthypuser=$9
staticip=${10}
host_file_name="inventory"

#------------------Destroy VM------------------
echo "Destroying VM: $vmname"
if ! grep -q "$hypervisoruser@$hypervisorip" $host_file_name
then
    # code if not found
    echo -e "[$hypervisoruser@$hypervisorip]\n$hypervisorip\n" >> $host_file_name
fi
ansible-playbook -i inventory delete_vm.yml -e "host=$hypervisoruser@$hypervisorip vmname=$vmname"
#-------------------Destroy VM--------------------
#------------------Update json------------------
echo "Updating json"
python updatejsondelete.py $net_name $hypervisorip $vmname
echo "Updating json done"
#------------------Update json------------------

#----------Update NS for Load Balancing---------
#TBD
#echo ./LoadBalancer.sh REM $mgmthypip $mgmthypuser $nsname $staticip $num_vm $vethIP
./LoadBalancer.sh REM $mgmthypip $mgmthypuser $nsname $staticip $num_vm $vethIP
#----------Update NS for Load Balancing---------
