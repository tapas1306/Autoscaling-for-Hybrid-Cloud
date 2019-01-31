import sys
from crontab import CronTab

#should do the following:
#1. read json and create the required setup on all hypervisors(Bridges, Namespace, Routes-NS&Host, NAT-NS&Host, veth)
#2. create tunnels
#3. call Action step for creating new VMs for each subnet.
#4. create cronjob and json
#
# These should be done only if not already done.

def main():
	if len(sys.argv) <= 1:
		print("Invalid argumets. Expect one argument: start/stop")
		exit()
	cron = CronTab(user="root")
	if sys.argv[1] == "start":
		#add cron after check
		#check
		iter2 = cron.find_comment('controller unique key')
		for item in iter2:
			print("Already running. Stop and try again")
			exit()
		job = cron.new(command='cd /root/autoscaler;ts=`date | tr -d \' \'`;python controller.py > logs/"$ts".log', comment='controller unique key')
		job.minute.every(5)
		cron.write()
	elif sys.argv[1] == "stop":
		#remove crons
		cron.remove_all(comment='controller unique key')
		cron.write()
if __name__ == '__main__':
	main()

