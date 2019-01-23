#!/bin/bash

if [ $# -lt 1 ] ; then
echo -e "Invalid input.\n\nUSAGE:\tmain.sh <Input Json File Name>\n"
exit
fi
cd $(dirname $0)
echo "Current Directory: "`pwd`

schemajson=$1
schemajson="$(basename $schemajson)"
echo "Using Input JSON file: "$schemajson
subnetcount=`cat $schemajson | jq -r '.Details[].Subnet' | wc -l`
hypcount=`cat mgmtdetails.json | jq -r '.HypervisorList[].IP' | wc -l`
hypcount=$((hypcount + 1))
if [ $subnetcount -eq 0 ] ; then
echo "No subnets found in the JSON Input file. Exiting with doing anything."
fi
TID=`cat tenant_count`
TID=$((TID + 1))
echo $TID > tenant_count
echo "Tenant ID: "$TID
host_file_name="inventory"
##################Creating Mgmt Network#####################
echo "Creating mgmt Network"
TNAME=`cat $schemajson | jq -r '.TName'`
mgmtName="C-"$TNAME
echo -e "<network>\n  <name>$mgmtName</name>\n  <forward mode='nat'/>\n  <bridge name='$mgmtName-br'/>\n  <ip address='192.$TID.0.1' netmask='255.255.0.0'>\n    <dhcp>\n      <range start='192.$TID.0.2' end='192.$TID.255.254'/>\n    </dhcp>\n  </ip>\n</network>\n" | sudo tee XMLs/$mgmtName.xml >>/dev/null
virsh net-define XMLs/$mgmtName.xml
virsh net-start $mgmtName
ip link set dev $mgmtName-br up
mgmthypervisorip=`cat mgmtdetails.json | jq -r '.mgmtHypervisor'`
mgmthypervisoruser=`cat mgmtdetails.json | jq -r '.mgmtHypervisorUser'`
for (( i=0; i<hypcount-1; i++ ))
do
hypervisoruser=`cat mgmtdetails.json | jq -r '.HypervisorList['$i'].User'`
hypervisorip=`cat mgmtdetails.json | jq -r '.HypervisorList['$i'].IP'`
hypervisorcount=`cat mgmtdetails.json | jq -r '.HypervisorList['$i'].Count'`
vxlancount=`cat vxlan_count`
if [ "$hypervisorip" = "$mgmthypervisorip" ] ; then
echo "Found main hypervisor in hypervisor list"
continue
fi
echo -e "<network>\n  <name>$mgmtName</name>\n  <forward mode='bridge'/>\n  <bridge name='$mgmtName-br'/>\n</network>\n" | sudo tee XMLs/$mgmtName-L2.xml >>/dev/null
if ! grep -q "$hypervisoruser@$hypervisorip" $host_file_name
then
    # code if not found
    echo -e "[$hypervisoruser@$hypervisorip]\n$hypervisorip\n" >> $host_file_name
fi
ansible-playbook -i $host_file_name create_network.yml -e "host=$hypervisoruser@$hypervisorip name=$mgmtName xmlname=XMLs/$mgmtName-L2.xml count=$hypervisorcount mgmthypip=$mgmthypervisorip vxcount=$vxlancount"
ip link add name $mgmtName-vx-$hypervisorcount type vxlan id $vxlancount dev $mgmtName-br remote $hypervisorip dstport 4789
ip link set dev $mgmtName-vx-$hypervisorcount up
vxlancount=$((vxlancount + 1))
echo $vxlancount > vxlan_count
done
echo "Created mgmt Network"
####################Creating mgmt Network###################
####################Creating NS########################
echo "Creating NS"
ip netns add $TNAME
ip link add name hyp$TNAME type veth peer name ${TNAME}hyp
ip link set dev ${TNAME}hyp netns $TNAME
vethIP=$TID.$TID.$TID.1
ip netns exec $TNAME ip addr add $vethIP/24 dev ${TNAME}hyp
ip addr add $TID.$TID.$TID.2/24 dev hyp${TNAME}
ip link set dev hyp${TNAME} up
ip netns exec $TNAME ip link set dev ${TNAME}hyp up
ip netns exec $TNAME ip route add default via $TID.$TID.$TID.2
echo "Created NS"
###################Creating NS############################
###################Creating subnets######################
echo "Creating subnets"
for (( i=0; i<subnetcount; i++ ))
do
subnetname=`cat $schemajson | jq -r '.Details['$i'].SubnetName'`
subnet=`cat $schemajson | jq -r '.Details['$i'].Subnet'`
mask=`cat $schemajson | jq -r '.Details['$i'].Mask'`
subnetname=$TNAME$subnetname

echo -e "<network>\n  <name>$subnetname</name>\n  <forward mode='bridge'/>\n  <bridge name='$subnetname-br'/>\n</network>\n" | sudo tee XMLs/$subnetname.xml >>/dev/null
brctl addbr $subnetname-br
virsh net-define XMLs/$subnetname.xml
virsh net-start $subnetname
ip link set dev $subnetname-br up
#create veth to ns
ip link add name $subnetname$TNAME type veth peer name ${TNAME}$subnetname
subnetgw=`echo $subnet | rev | cut -c 2- | rev`
subnetgw=$subnetgw'1'
ip link set dev ${TNAME}$subnetname netns $TNAME
ip netns exec $TNAME ip addr add $subnetgw/24 dev ${TNAME}$subnetname
ip netns exec $TNAME ip link set dev ${TNAME}$subnetname up
brctl addif $subnetname-br $subnetname$TNAME
ip link set dev $subnetname$TNAME up
for (( j=0; j<hypcount-1; j++ ))
do
hypervisoruser=`cat mgmtdetails.json | jq -r '.HypervisorList['$j'].User'`
hypervisorip=`cat mgmtdetails.json | jq -r '.HypervisorList['$j'].IP'`
hypervisorcount=$((hypervisorcount + 1))
vxlancount=`cat vxlan_count`
if [ "$hypervisorip" = "$mgmthypervisorip" ] ; then
echo "Found main hypervisor in hypervisor list"
continue
fi
if ! grep -q "$hypervisoruser@$hypervisorip" $host_file_name
then
    # code if not found
    echo -e "[$hypervisoruser@$hypervisorip]\n$hypervisorip\n" >> $host_file_name
fi
ansible-playbook -i $host_file_name create_network.yml -e "host=$hypervisoruser@$hypervisorip name=$subnetname xmlname=XMLs/$subnetname.xml count=$hypervisorcount mgmthypip=$mgmthypervisorip vxcount=$vxlancount"
ip link add name $subnetname-vx-$hypervisorcount type vxlan id $vxlancount dev $subnetname-br remote $hypervisorip dstport 4789
ip link set dev $subnetname-vx-$hypervisorcount up
vxlancount=$((vxlancount + 1))
echo $vxlancount > vxlan_count
done
done
echo "Created subnets"
###################Created Subnets#########################
###################Create Controller#######################
#------------------Create VM------------------
vmname='CVM'$TNAME
echo "Creating new VM: $vmname"
prefixstr="    \<interface type='network'\>
      \<source network='"
postfixstr="'\/\>
    \<\/interface\>
"
netcmd="${prefixstr}$mgmtName${postfixstr}"
mkdir -p XMLs
cp -f vmtemplate.xml XMLs/$vmname.xml
perl -p -i -e "s/\{\{NETWORKPLACEHOLDER\}\}/${netcmd}/g" XMLs/$vmname.xml
sed -i -e "s/{{VMNAME}}/$vmname/g" XMLs/$vmname.xml
imgpath="\/var\/lib\/libvirt\/images\/$vmname.img"
perl -p -i -e "s/\{\{VMPATH\}\}/$imgpath/g" XMLs/$vmname.xml
echo "Copying image file"
cp cvmtemplate.img /var/lib/libvirt/images/$vmname.img
echo "Done copying image file"
fullxmlpath=`pwd`/XMLs/$vmname.xml
imgpath=`cat mgmtdetails.json | jq -r '.ControllerImgPath'`
ansible-playbook -i inventory create_vm.yml -e "host=localhost vmname=$vmname xmlname=$fullxmlpath imgpath=$imgpath"
echo "Sleeping for two minutes for the VM to boot"
sleep 120
echo "I'm back up now. Trying 15 times at 30 second interval"
#-------------------Create VM--------------------
str=`python getmgmtIPandens3MAC.py $mgmthypervisorip $mgmthypervisoruser $vmname`
tempArr=(${str//;/ })
controller_ip=${tempArr[0]}
if ! grep -q "root@$controller_ip" $host_file_name
then
    # code if not found
    echo -e "[root@$controller_ip]\n$controller_ip\n" >> $host_file_name
fi
sshpubkey=`cat /root/.ssh/id_rsa.pub`
echo $sshpubkey > XMLs/$vmname.pub
ansible-playbook -i inventory add_ssh_key.yml -e "host=root@$controller_ip sshpubkeyfile=XMLs/$vmname.pub"

#ssh should work without passwords now.
jq '.ControllerIP = "'$controller_ip'"' mgmtdetails.json > tmp.$$.json && mv tmp.$$.json mgmtdetails.json
jq '.ControllerNetworkName = "'$mgmtName'"' mgmtdetails.json > tmp.$$.json && mv tmp.$$.json mgmtdetails.json
jq '.vethIP = "'$vethIP'"' mgmtdetails.json > tmp.$$.json && mv tmp.$$.json mgmtdetails.json
cp mgmtdetails.json ../autoscaler/
cp $schemajson ../autoscaler/
scp -o StrictHostKeyChecking=no -r ../autoscaler root@$controller_ip:~/
echo "Copied files to controller"
#ssh root@$controller_ip /root/autoscaler/setup_ssh.sh
#ssh root@$controller_ip /root/autoscaler/initialize_controller.py

echo "My job here is done! Controller will take over now. Bye!"

