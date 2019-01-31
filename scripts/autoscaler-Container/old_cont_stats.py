import os
import subprocess
import sys
import docker 

def cont_cpu_stats():
	
	list_ = sys.argv[1]
	cont_list = list_.split(",")
        total_cpu =0
        hyp_cont_cpu =[]
        cont_cpu_stats={}
        os.system("sudo docker stats --no-stream > /home/ece792/dockerstats")
        with open("dockerstats",'r') as f:
        	for row in f:
                	list = row.strip('\n').split()
                	id_ =str(list[0])
                	cont_cpu_stats[id_[:10]] =list[1]

        client = docker.from_env()
        for item in cont_list:
		if item is not "":
                	cont_id = str(client.containers.get(item).short_id)
                	if cont_id in cont_cpu_stats:
                        	hyp_cont_cpu.append(cont_cpu_stats[cont_id])

        for i in range(len(hyp_cont_cpu)):
                total_cpu = total_cpu + float(hyp_cont_cpu[i].strip("%"))

        cont_cpu_avg = total_cpu/(len(hyp_cont_cpu))

        print cont_cpu_avg



def main():
        cont_cpu_stats()


if __name__ == '__main__':
        main()

