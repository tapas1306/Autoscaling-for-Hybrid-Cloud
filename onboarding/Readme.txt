
##########################################################################################

Usage :
	./main.sh <<input-json-file-name>>

Input File:

The input file needs to provide the tenant details like number of initial VM's to be spawned, the maximum and minimum threshold time, cool-down period. For sample input, please refer <<sample-schema.json>>.

Also provide the list of all Hypervisor's, the tenant wants the network to be spawned upon. The autoscaling will happen across the list of Hypervisors provided in this list.

This will get the tenant/service-provider's network up and running.

##########################################################################################
