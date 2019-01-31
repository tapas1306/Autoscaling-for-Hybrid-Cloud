import sys
import json

with open('schema_con.json') as f:
    data = json.load(f)

found = False
for item in data["Details"]:
    if item["SubnetName"] == sys.argv[1]:
        for seconditem in item["ConList"]:
            if seconditem["Hypervisor"] == sys.argv[2]:
                seconditem["List"] = [newitem for newitem in seconditem["List"] if newitem["Name"] != sys.argv[3]]
                #decrease con count
                item["num_cons"] = str((int(item["num_cons"]) - 1))
                item["num_scaled_cons"] = str((int(item["num_scaled_cons"]) - 1))
		if int(item["num_scaled_cons"]) == 0:
			item["status"] = "idle"
                found = True
                break
        if found == True:
            break
with open('schema_con.json', 'w') as outfile:
    json.dump(data, outfile,indent = 4)
