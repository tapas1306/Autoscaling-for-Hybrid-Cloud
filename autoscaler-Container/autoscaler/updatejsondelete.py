import sys
import json

with open('schema.json') as f:
    data = json.load(f)

found = False
for item in data["Details"]:
    if item["SubnetName"] == sys.argv[1]:
        for seconditem in item["VMList"]:
            if seconditem["Hypervisor"] == sys.argv[2]:
                seconditem["List"] = [newitem for newitem in seconditem["List"] if newitem["Name"] != sys.argv[3]]
                #decrease vm count
                item["num_vms"] = str((int(item["num_vms"]) - 1))
                item["num_scaled_vms"] = str((int(item["num_scaled_vms"]) - 1))
		if int(item["num_scaled_vms"]) == 0:
			item["status"] = "idle"
                found = True
                break
        if found == True:
            break
with open('schema.json', 'w') as outfile:
    json.dump(data, outfile,indent = 4)
