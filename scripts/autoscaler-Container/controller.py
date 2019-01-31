
import sh
import sys,os
import subprocess
import shlex
import time
import glob
import json


def cont_cpu_stats(cont_list, hypUser, hypIP):

        list_ =''
        for item in cont_list:
                list_ =item+','+list_

        os.system("scp cont_stats.py "+ hypUser+"@"+hypIP+":~/")
        output = subprocess.check_output('ssh' + ' ' + hypUser + '@' + hypIP + ' ' + 'sudo python -W ignore  cont_stats.py '+list_,shell =True)
        return float(output.strip().split(",")[0])

def getcpustats_hyp(hyp_IP, uname):
        uptime = sh.Command("/usr/bin/ssh")
        command_string = "uptime"
        result = uptime("-o StrictHostKeyChecking=no",uname+"@"+hyp_IP, command_string)
        result = str(result)
        #print (result)
        result = result.split()
        #print (result)
        cpu_15min = result[11].split(",")[0]
        return cpu_15min

def findNewHyp(mgmtdata, hyp_th):
        for item in mgmtdata["HypervisorList"]:
                hypIP = item["IP"]
                uname = item["User"]
                cpu_percent = getcpustats_hyp(hypIP, uname)
                if float(cpu_percent) < float(hyp_th):
			print("New Hyprvisor: " + hypIP + ", CPU Usage: " + cpu_percent);
                        return hypIP
        print("Fatal Error. No hypervisors available to scale.")
        return

def scalingdecision(con_dict, max, min, status, scaleuptime, cooldownperiod, hypIP):
	#return 0 - No action, 1 - scale up, 2 - scale down
	#stealtime = getstealtime(vmname)
	cont_list = []
	for item in con_dict:
		cont_list.append(item["Name"])
	cpu_load = cont_cpu_stats(cont_list, "root", hypIP)
        cpu_percent = getcpustats_hyp(hypIP, "root")
        print("CPU load ", float(cpu_load), cpu_percent)
	if cpu_load > float(max):
		return 1
	elif cpu_load < float(min):
		if status == "scaledup":
			currenttime = int(round(time.time()))
			sut = int(scaleuptime)
			cdp = int(cooldownperiod)
			if currenttime <= (sut + cdp):
				#in cooldown
				print("In cooldown period. Skipping")
				return 0
			return 2
		return 0
	elif cpu_load >= float(min):
                return 0
	#not enter here

def findUser(mgmtdata, newHypIP):
	for mitem in mgmtdata["HypervisorList"]:
		if newHypIP == mitem["IP"]:
			return mitem["User"]

def SDCheckAllHypervisors(ConList, min_load):
        for item in ConList:
                hypIP = item["Hypervisor"]
                if len(item["List"]) == 0:
                        continue
                load = getcpustats_hyp(hypIP, "root")
                if float(load) > float(min_load):
                        print("Found an hypervisor with load greater than minimum load: " + hypIP , load, min_load)
                        return False
        print("No overloaded hypervisors. Scaling down.")
        return True

def findSDCon(details):
        num_scaled_cons = details["num_scaled_cons"]
        for item in details["ConList"]:
                hypIp = item["Hypervisor"]
                for seconditem in item["List"]:
                        if seconditem["ScaledUpOrder"] == num_scaled_cons:
                                return (hypIp, seconditem["Name"], seconditem["IP"])
        print("Fatal Error! Check JSON for scaled up order and num scaled cons")

def main():
	#cronjob run every minute (configurable?) steps:
	#check first VM's steal-time in a subnet in a hypervisor.
	#decide. Add or remove. Call action.
	print("Controller started at Time:" + str(time.time()))
	with open('schema_con.json') as f:
		schema = json.load(f)
	with open('mgmtdetails.json') as g:
		mgmtdata = json.load(g)
	mgmthypip = mgmtdata["mgmtHypervisor"]
	mgmthypuser = mgmtdata["mgmtHypervisorUser"]
	for item in schema["Details"]:
		for seconditem in item["ConList"]:
			hypIP = seconditem["Hypervisor"]
			if len(seconditem["List"]) == 0:
				continue
			tmpDict = seconditem["List"]
			#Scaling: 0 - No action, 1 - Scale up, 2 - scale down
			decision = scalingdecision(tmpDict,item["max_load"],item["min_load"],item["status"], item["scaleuptime"], item["cooldownperiod"], seconditem["Hypervisor"]) #TBD
			if decision == 0:
				print("All Good. Nothing to do")
				continue
			elif decision == 1:
				#scaleup
				print("Scaling up")
				newHypIP = findNewHyp(mgmtdata, item["max_hyp_load"]) #TBD
				newHypUser = findUser(mgmtdata, newHypIP) #TBD
				newConPrefix = mgmtdata["ConPrefix"]
				#newVMName = schema["TName"] + item["SubnetName"] + newVMPrefix + str((int(item["num_vms"]) + 1)) #changed on demand from trmallic
				newConNum = str((int(item["num_cons"]) + 1))
				newConName =  item["NetName"] + newConPrefix + newConNum
				NSName = schema["TName"]
			#	print('./scale_up.sh ' + newHypIP + ' ' + newHypUser + ' ' + newVMName + ' ' + item["SubnetName"] + ' ' + mgmtdata["ControllerNetworkName"] + ' ' + mgmtdata["ControllerIP"] + ' ' + NSName + ' ' + newVMNum + ' ' + mgmtdata["vethIP"] + ' ' + mgmthypip + ' ' + mgmthypuser)
				subprocess.call(shlex.split('./scale_up.sh ' + newHypIP + ' ' + newHypUser + ' ' + newConName + ' ' + item["SubnetName"] + ' ' + mgmtdata["ControllerNetworkName"] + ' ' + mgmtdata["ControllerIP"] + ' ' + NSName + ' ' + newConNum + ' ' + mgmtdata["vethIP"] + ' ' + mgmthypip + ' ' + mgmthypuser + ' ' + item["image_name"] + ' ' + item["NetName"]))
				break
			elif decision == 2:
				#scaledown
				print("Scaling down")
                                if not SDCheckAllHypervisors(item["ConList"], float(item["min_load"])):
                                        print("Other Hypervisors have load. Won't scale down")
                                        continue
				(SDhypIP, SDConName, SDConIP) = findSDCon(item)
				SDhypUser = findUser(mgmtdata, SDhypIP)
				LBConNum = item["num_cons"]
				subprocess.call(shlex.split('./scale_down.sh ' + SDhypIP + ' ' + SDhypUser + ' ' + SDConName + ' ' + item["SubnetName"] + ' ' + schema["TName"] + ' ' + LBConNum + ' ' + mgmtdata["vethIP"] + ' ' + mgmthypip + ' ' + mgmthypuser + ' ' + SDConIP))
				break
			else:
				print("Fatal error: scaler failed")
				exit()

if __name__ == '__main__':
	main()
