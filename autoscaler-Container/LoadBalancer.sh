#!/bin/bash

add=$1
hypIP=$2
hypUser=$3
NSname=$4
VMIP=$5
NoVMs=$6
NSIP=$7

if [ $add == 'ADD' ] ; then
	ssh $hypUser@$hypIP sudo ip netns exec $NSname iptables -I PREROUTING -t nat -p tcp -d $NSIP  -m statistic --mode nth --every $NoVMs --packet 0 -j DNAT --to-destination $VMIP:22
elif [ $add == 'REM' ] ; then
	ssh $hypUser@$hypIP sudo ip netns exec $NSname iptables -D PREROUTING -t nat -p tcp  -d $NSIP  -m statistic --mode nth --every $NoVMs --packet 0 -j DNAT --to-destination $VMIP:22
fi
