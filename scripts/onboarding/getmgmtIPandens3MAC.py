import libvirt
import sys
import time

def getMgmtIp(hypIp, hypUser, guestName):
    conn = libvirt.open("qemu+ssh://" + hypUser + "@" + hypIp + "/system?no_verify=1")
    dom = conn.lookupByName(guestName)
    mac=""
    ip=""
    ifaces = dom.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_AGENT, 0)
    for (name, val) in ifaces.iteritems():
        if name == "ens3":
            mac=val['hwaddr']
            for ipaddr in val['addrs']:
                if ipaddr['type'] == libvirt.VIR_IP_ADDR_TYPE_IPV4:
                    ip = ipaddr['addr']
    print(ip+";"+mac)

count = 1
while True:
    try:
        getMgmtIp(sys.argv[1],sys.argv[2],sys.argv[3])
        break
    except  Exception as e:
        print(e)
        count = count + 1
        if count > 15:
            print("error")
            break
        time.sleep(30)

