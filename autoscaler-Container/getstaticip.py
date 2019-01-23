import libvirt
import sys
import json

with open('schema.json') as f:
    data = json.load(f)
newsubnet = ""
for item in data["Details"]:
    if item["SubnetName"] == sys.argv[1]:
        foundnewSubnet = False
        subnet = item["Subnet"]
        mask = item["Mask"]
        subnetstore = subnet.split(".")
        lastoctet = int(subnetstore[3])
        gw = subnetstore[0] + "." + subnetstore[1] + "." + subnetstore[2] + "." + str(lastoctet + 1)
        while True:
            lastoctet = lastoctet + 1
            while lastoctet < 3:
                lastoctet = lastoctet + 1
            if lastoctet > 255:
                #TBD
                break
            newsubnet = subnetstore[0] + "." + subnetstore[1] + "." + subnetstore[2] + "." + str(lastoctet)
            dontUseThisNewSubnet = False
            for seconditem in item["VMList"]:
                for thirditem in seconditem["List"]:
                    if newsubnet == thirditem["IP"]:
                        dontUseThisNewSubnet = True
                        break
                if dontUseThisNewSubnet == True:
                    break
            if dontUseThisNewSubnet == False:
                foundNewSubnet = True
                break
        if foundNewSubnet == True:
            print(newsubnet + ";" + mask + ";" + gw)
        else:
            print("error")
        break

