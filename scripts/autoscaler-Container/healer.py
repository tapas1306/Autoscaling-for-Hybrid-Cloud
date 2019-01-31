
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
	try:
        	os.system("scp cont_stats.py "+ hypUser+"@"+hypIP+":~/")
        	output = subprocess.check_output('ssh' + ' ' + hypUser + '@' + hypIP + ' ' + '"sudo python -W ignore  cont_stats.py '+list_ + '"',shell =True)
	except Exception as e:
		print("Hypervisor down")
		str = ",".join(cont_list)
		str = "0.00," + str
		return str
        return output.strip()

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
#	return "192.168.50.66"
        for item in mgmtdata["HypervisorList"]:
                hypIP = item["IP"]
                uname = item["User"]
                cpu_percent = getcpustats_hyp(hypIP, uname)
                if float(cpu_percent) < float(hyp_th):
                        return hypIP
        print("Fatal Error. No hypervisors available to scale.")
        return

def getAffectedContainers(all_con_list, hypIP):
	cont_list = []
	for item in all_con_list:
		cont_list.append(item["Name"])
	return cont_cpu_stats(cont_list, "root", hypIP).split(",")[1:]

def findUser(mgmtdata, newHypIP):
	for mitem in mgmtdata["HypervisorList"]:
		if newHypIP == mitem["IP"]:
			return mitem["User"]

def removeconfromschema(subnetname,hypIP,conname):
	with open('schema_con.json', 'r') as f:
		schema = json.load(f)
	found = False
	for item in schema["Details"]:
		if item["SubnetName"] != subnetname:
			continue
		for seconditem in item["ConList"]:
			if seconditem["Hypervisor"] == hypIP:
				seconditem["List"] = [newitem for newitem in seconditem["List"] if newitem["Name"] != conname]
				found = True
				break
		if found == True:
			break
	with open('schema_con.json', 'w') as outfile:
		json.dump(schema, outfile,indent = 4)

def addcontoschema(subnetname,hypIP,conname,conip,conmgmtip,conscaledresource,connum):
	with open('schema_con.json', 'r') as f:
		schema = json.load(f)
	found = False
	for item in schema["Details"]:
		if item["SubnetName"] != subnetname:
			continue
		for seconditem in item["ConList"]:
			if seconditem["Hypervisor"] == hypIP:
				tmpDict = {}
				tmpDict["Name"] = conname
				tmpDict["IP"] = conip
				tmpDict["mgmtIP"] = conmgmtip
				tmpDict["ScaledUpResource"] = conscaledresource
				tmpDict["ScaledUpOrder"] = connum
				seconditem["List"].append(tmpDict)
				found = True
				break
		if found == True:
			break
	with open('schema_con.json', 'w') as outfile:
		json.dump(schema, outfile,indent = 4)

def main():
	#cronjob run every minute (configurable?) steps:
	#check first VM's steal-time in a subnet in a hypervisor.
	#decide. Add or remove. Call action.
	print("Healer started at Time:" + str(time.time()))
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
			conlist = seconditem["List"]
			#Scaling: 0 - No action, 1 - Scale up, 2 - scale down
			failed_cons_list = getAffectedContainers(conlist, seconditem["Hypervisor"]) #TBD
			print("Failed Containers: " + str(failed_cons_list))
			for failed_con in failed_cons_list:
				if failed_con == '':
					print("All Good. Nothing to do")
					continue
				#getdetails
				failed_con_ip = ''
				failed_con_num = ''
				failed_con_scaled_resource = ''
				failed_con_mgmt_ip = ''
				for tmpitem in conlist:
					if tmpitem["Name"] == failed_con:
						print("Found the one to delete in the schema.json.")
						failed_con_ip = tmpitem["IP"]
						failed_con_num = tmpitem["ScaledUpOrder"]
						failed_con_scaled_resource = tmpitem["ScaledUpResource"]
						failed_con_mgmt_ip = tmpitem["mgmtIP"]
						break
				if failed_con_ip == '':
					print("Failed to find the failed container in the schema.json. Tampered it? Moving on.")
					continue
				#scaledown
				print("Removing failed container: " + failed_con)
				oldHypUser = findUser(mgmtdata, seconditem["Hypervisor"])
				subprocess.call(shlex.split('./scale_down.sh ' + seconditem["Hypervisor"] + ' ' + oldHypUser + ' ' + failed_con + ' ' + item["SubnetName"] + ' ' + schema["TName"] + ' ' + failed_con_num + ' ' + mgmtdata["vethIP"] + ' ' + mgmthypip + ' ' + mgmthypuser + ' ' + failed_con_ip + ' No No'))
				removeconfromschema(item["SubnetName"],seconditem["Hypervisor"],failed_con)
				#scaleup
				print("Creating failed container: " + failed_con)
				newHypIP = findNewHyp(mgmtdata, item["max_hyp_load"]) #TBD
				newHypUser = findUser(mgmtdata, newHypIP) #TBD
				newConPrefix = mgmtdata["ConPrefix"]
				#newVMName = schema["TName"] + item["SubnetName"] + newVMPrefix + str((int(item["num_vms"]) + 1)) #changed on demand from trmallic
				newConNum = failed_con_num
				newConName =  failed_con
				NSName = schema["TName"]
			#	print('./scale_up.sh ' + newHypIP + ' ' + newHypUser + ' ' + newVMName + ' ' + item["SubnetName"] + ' ' + mgmtdata["ControllerNetworkName"] + ' ' + mgmtdata["ControllerIP"] + ' ' + NSName + ' ' + newVMNum + ' ' + mgmtdata["vethIP"] + ' ' + mgmthypip + ' ' + mgmthypuser)
				subprocess.call(shlex.split('./scale_up.sh ' + newHypIP + ' ' + newHypUser + ' ' + newConName + ' ' + item["SubnetName"] + ' ' + mgmtdata["ControllerNetworkName"] + ' ' + mgmtdata["ControllerIP"] + ' ' + NSName + ' ' + newConNum + ' ' + mgmtdata["vethIP"] + ' ' + mgmthypip + ' ' + mgmthypuser + ' ' + item["image_name"] + ' ' + item["NetName"] + ' No No'))
				addcontoschema(item["SubnetName"],newHypIP,failed_con,failed_con_ip,failed_con_mgmt_ip,failed_con_scaled_resource,failed_con_num)

if __name__ == '__main__':
	main()
