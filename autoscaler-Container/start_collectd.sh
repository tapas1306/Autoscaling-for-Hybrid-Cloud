#/bin/bash
#args: vmname vmip serverip
echo "User: "`whoami`
project_dir=`pwd`
host_file_name="inventory"
vmname=$1
vmip=$2
serverip=$3
sudo cp $project_dir/collectd/collectd-sample.conf $project_dir/collectd/$vmname-collectd.conf
sed -i -e 's/Hostname.*/Hostname \"'$vmname'\"/g' $project_dir/collectd/$vmname-collectd.conf
sed -i -e 's/Server.*/Server \"'$serverip'\" \"25826\"/g' $project_dir/collectd/$vmname-collectd.conf

if grep -q "$vmname" $host_file_name
then
    # code if found
    sed -i '/'$vmname'/,+1 d' $host_file_name
fi
echo -e "[$vmname]\n$vmip\n" >> $host_file_name
sudo ansible-playbook -i $host_file_name collectd.yml -e "vmname=$vmname host_key_checking=False"
