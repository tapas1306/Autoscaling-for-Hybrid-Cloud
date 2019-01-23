import sys,os
import subprocess
import shlex
import time
import glob
import json
from pprint import pprint

def main():
	print("Initialize Controller started at Time:" + str(time.time()))
	with open('schema.json') as f:
		schema = json.load(f)
	with open('mgmtdetails.json') as g:
		mgmtdata = json.load(g)
	mgmthypip = mgmtdata["mgmtHypervisor"]
	mgmthypuser = mgmtdata["mgmtHypervisorUser"]
	for item in schema["Details"]:
		item["SubnetName"] = schema["TName"] + item["SubnetName"]
		item["status"] = "idle"
		num_vms = item["num_vms"]
		item["num_vms"] = "0"
		item["scaleuptime"] = ""
		item["num_scaled_vms"] = "0"
		tmpList = list()
		for mitem in mgmtdata["HypervisorList"]:
			tmpDict = {"Hypervisor": mitem["IP"], "List": []}
			tmpList.append(tmpDict)
		item["VMList"] = tmpList
		with open('schema.json', 'w') as h:
			json.dump(schema, h,indent = 4)
		#pprint(item)
		for i in range(0,int(num_vms)):
			newVMName = item["SubnetName"] + mgmtdata["VMPrefix"] + str(i+1)
			NSName = schema["TName"]
			subprocess.call(shlex.split('./scale_up.sh ' + mgmthypip + ' ' + mgmthypuser + ' ' + newVMName + ' ' + item["SubnetName"] + ' ' + mgmtdata["ControllerNetworkName"] + ' ' + mgmtdata["ControllerIP"] + ' ' + NSName + ' ' + str(i+1) + ' ' + mgmtdata["vethIP"] + ' ' + mgmthypip + ' ' + mgmthypuser))
	with open('schema.json') as i:
                schema = json.load(i)
	for item in schema["Details"]:
		item["status"] = "idle"
		item["scaleduptime"] = ""
		item["num_scaled_vms"] = 0
	with open('schema.json','w') as j:
		json.dump(schema, j,indent = 4)	

if __name__ == '__main__':
	main()
