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
        missing_cont =[]

        os.system("sudo docker stats --no-stream > dockerstats")
        with open("dockerstats",'r') as f:
                for row in f:
                        list = row.strip('\n').split()
                        id_ =str(list[0])
                        cont_cpu_stats[id_[:10]] =list[1]

        client = docker.from_env()
        for item in cont_list:
                if item is not "":
                        try:
                                cont_id = str(client.containers.get(item).short_id)
			except docker.errors.NotFound as e:
                                missing_cont.append(item)

                        except docker.errors.APIError as e:
                                missing_cont.append(item)

			except Exception as e:
				missing_cont.append(item)

                        else:
                                if cont_id in cont_cpu_stats:
                                        hyp_cont_cpu.append(cont_cpu_stats[cont_id])
				else:
					missing_cont.append(item)

        for i in range(len(hyp_cont_cpu)):
                  total_cpu = total_cpu + float(hyp_cont_cpu[i].strip("%"))

	try :
                cont_cpu_avg = total_cpu/(len(hyp_cont_cpu))
        except ZeroDivisionError :
                cont_cpu_avg =float(0)	

        #print missing_cont

        miss_cont = ','.join(missing_cont)

        print str(cont_cpu_avg)+","+miss_cont



def main():
        cont_cpu_stats()


if __name__ == '__main__':
        main()


