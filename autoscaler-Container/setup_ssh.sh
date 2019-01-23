#!/bin/bash
##TBD
cd /root/autoscaler
hypcount=`cat mgmtdetails.json | jq -r '.HypervisorList[].IP' | wc -l`
yes y |ssh-keygen -q -t rsa -N '' >/dev/null
sshpubkey=`cat /root/.ssh/id_rsa.pub`
cat $sshpubkey > XMLs/$vmname.pub
ansible-playbook -i inventory add_ssh_key.yml -e "host=$root@$controller_ip sshpubkeyfile=XMLs/$vmname.pub"
