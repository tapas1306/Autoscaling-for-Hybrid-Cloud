import sys,os
import subprocess
import shlex
import time
import glob
import json

def getstealtime(vmname):
	#return 1 on overloaded and 0 otherwise
	collectdpath = "/var/lib/collectd/"
	pathaftervmname = "/cpu/"
	stfilenameprefix = "percent-steal"
	list_of_files = glob.glob(collectdpath + vmname + pathaftervmname + stfilenameprefix + '*')
	latest_file = max(list_of_files, key=os.path.getctime)
#	print("Using File : " + latest_file)
	last = ""
	with open(latest_file, 'rb') as fh:
		#if sum(1 for line in fh) == 1:
		#	print("error")
		#	return -1
		line=""
		count = 0
		for line in fh:
			count += 1
			pass
		if count < 2:
			print("error")
			return -1
		last = line
	stealtime = float(last.split(",")[1])
#	print("st: "+ str(stealtime))
	return stealtime

def findNewHyp(schema, subnetname):
#	return "192.168.50.66"
	for item in schema["Details"]:
		if item["SubnetName"] != subnetname:
			continue
		for seconditem in item["VMList"]:
			hypIP = seconditem["Hypervisor"]
			if len(seconditem["List"]) == 0:
				return hypIP
			stealtime = getstealtime(seconditem["List"][0]["Name"])
			if stealtime < float(item["min_st"]):
				return hypIP
		print("Warning. No hypervisor with lower steal time than min threshold available. Finding one below max threshold.")
		for seconditem in item["VMList"]:
			hypIP = seconditem["Hypervisor"]
			if len(seconditem["List"]) == 0:
				return hypIP
			stealtime = getstealtime(seconditem["List"][0]["Name"])
			if stealtime < float(item["max_st"]):
				return hypIP
		print("Fatal Error. No hypervisors available to scale.")
		return

def scalingdecision(vmname, max, min, status, scaleuptime, cooldownperiod):
	#return 0 - No action, 1 - scale up, 2 - scale down
	#stealtime = getstealtime(vmname)
	stealtime = getstealtime(vmname)
	if stealtime > float(max):
		return 1
	elif stealtime < float(min):
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
	elif stealtime >= float(min):
		return 0
	#not enter here
	print("Scalingdecision: Something's not right. Unable to make a decision")
	return -1

def findUser(mgmtdata, newHypIP):
	for mitem in mgmtdata["HypervisorList"]:
		if newHypIP == mitem["IP"]:
			return mitem["User"]

def SDCheckAllHypervisors(VMList, min_st):
	for item in VMList:
                hypIP = item["Hypervisor"]
                if len(item["List"]) == 0:
                        continue
                stealtime = getstealtime(item["List"][0]["Name"])
                if stealtime > min_st:
			print("Found an hypervisor with load greater than steal time: " + hypIP)
                        return False
	print("No overloaded hypervisors. Scaling down.")
	return True

def findSDVM(details):
	num_scaled_vms = details["num_scaled_vms"]
	for item in details["VMList"]:
		hypIp = item["Hypervisor"]
		for seconditem in item["List"]:
			if seconditem["ScaledUpOrder"] == num_scaled_vms:
				return (hypIp, seconditem["Name"], seconditem["IP"])
	print("Fatal Error! Check JSON for scaled up order and num scaled vms")

def main():
	#cronjob run every minute (configurable?) steps:
	#check first VM's steal-time in a subnet in a hypervisor.
	#decide. Add or remove. Call action.
	print("Controller started at Time:" + str(time.time()))
	with open('schema.json') as f:
		schema = json.load(f)
	with open('mgmtdetails.json') as g:
		mgmtdata = json.load(g)
	mgmthypip = mgmtdata["mgmtHypervisor"]
	mgmthypuser = mgmtdata["mgmtHypervisorUser"]
	for item in schema["Details"]:
		for seconditem in item["VMList"]:
			hypIP = seconditem["Hypervisor"]
			print("Hypervisor: " + hypIP)
			if len(seconditem["List"]) == 0:
				print("No VMs in this Hypervisor")
				continue
			tmpDict = seconditem["List"][0]
			#Scaling: 0 - No action, 1 - Scale up, 2 - scale down
			decision = scalingdecision(tmpDict["Name"],item["max_st"],item["min_st"],item["status"], item["scaleuptime"], item["cooldownperiod"]) #TBD
#			decision = 1
			if decision == 0:
				print("All Good. Nothing to do")
				print("----------------------------")
				continue
			elif decision == 1:
				#scaleup
				print("Scaling up")
				newHypIP = findNewHyp(schema, item["SubnetName"]) #TBD
				newHypUser = findUser(mgmtdata, newHypIP) #TBD
				newVMPrefix = mgmtdata["VMPrefix"]
				#newVMName = schema["TName"] + item["SubnetName"] + newVMPrefix + str((int(item["num_vms"]) + 1)) #changed on demand from trmallic
				newVMName =  item["SubnetName"] + newVMPrefix + str((int(item["num_vms"]) + 1))
				NSName = schema["TName"]
				newVMNum = str((int(item["num_vms"]) + 1))
			#	print('./scale_up.sh ' + newHypIP + ' ' + newHypUser + ' ' + newVMName + ' ' + item["SubnetName"] + ' ' + mgmtdata["ControllerNetworkName"] + ' ' + mgmtdata["ControllerIP"] + ' ' + NSName + ' ' + newVMNum + ' ' + mgmtdata["vethIP"] + ' ' + mgmthypip + ' ' + mgmthypuser)
				subprocess.call(shlex.split('./scale_up.sh ' + newHypIP + ' ' + newHypUser + ' ' + newVMName + ' ' + item["SubnetName"] + ' ' + mgmtdata["ControllerNetworkName"] + ' ' + mgmtdata["ControllerIP"] + ' ' + NSName + ' ' + newVMNum + ' ' + mgmtdata["vethIP"] + ' ' + mgmthypip + ' ' + mgmthypuser))
				break
			elif decision == 2:
				#scaledown
				print("Scaling down")
				if not SDCheckAllHypervisors(item["VMList"], float(item["min_st"])):
					print("Other Hypervisors have load. Won't scale down")
					continue
				(SDhypIP, SDvmName, SDvmIP) = findSDVM(item)
				SDhypUser = findUser(mgmtdata, SDhypIP)
				LBVMNum = item["num_vms"]
				subprocess.call(shlex.split('./scale_down.sh ' + SDhypIP + ' ' + SDhypUser + ' ' + SDvmName + ' ' + item["SubnetName"] + ' ' + schema["TName"] + ' ' + LBVMNum + ' ' + mgmtdata["vethIP"] + ' ' + mgmthypip + ' ' + mgmthypuser + ' ' + SDvmIP))
				break
			else:
				print("Fatal error: scaler failed")
				exit()

if __name__ == '__main__':
	main()
