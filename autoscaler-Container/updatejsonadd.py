import sys
import json
import time

with open('schema.json') as f:
    data = json.load(f)

found = False
for item in data["Details"]:
    if item["SubnetName"] == sys.argv[1]:
        for seconditem in item["VMList"]:
            if seconditem["Hypervisor"] == sys.argv[2]:
                tmpDict = {}
                tmpDict["Name"]=sys.argv[3]
                tmpDict["IP"]=sys.argv[4]
                tmpDict["mgmtIP"]=sys.argv[5]
		tmpDict["ScaledUpResource"]="yes"
		tmpDict["ScaledUpOrder"]=str((int(item["num_scaled_vms"]) + 1))
                seconditem["List"].append(tmpDict)
                #increase vm count
                item["num_vms"] = str((int(item["num_vms"]) + 1))
                item["num_scaled_vms"] = str((int(item["num_scaled_vms"]) + 1))
		item["scaleuptime"] = str(int(round(time.time())))
		item["status"] = "scaledup"
                found = True
                break
        if found == True:
            break
if found == False:
    print("error")
    exit()
with open('schema.json', 'w') as outfile:
    json.dump(data, outfile,indent = 4)
