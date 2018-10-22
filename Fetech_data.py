import io
import re
import string
import os
import paramiko
import MySQLdb

ontap = ['#### Enter the Switch IP or Hostnamae']


word = "cluster_mgmt"
Server_Info = {}
flash_Info = {}
Cluster_Info = {}
service_ps_ipv4 = {}
version = {}

#Enable this section when IPv6 required for Service Processor
#service_ps_ipv6 = {}
modelinfo ={}
sub = '10.65.59.'
ip = 'IPv4'
model1='AFF'
model2='FAS'

#Run different command into the linux machine
for i in ontap:
    ssh = paramiko.SSHClient()
    
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(i, username='admin', password='netapp01')

    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('network interface show -role cluster-mgmt -fields address')
    ssh_stdin_c, ssh_stdout_c, ssh_stderr_c = ssh.exec_command('network interface show -role node-mgmt')
    ssh_stdin_s, ssh_stdout_s, ssh_stderr_s = ssh.exec_command('service-processor network show -node * -fields ip-address')
    ssh_stdin_m, ssh_stdout_m, ssh_stderr_m = ssh.exec_command('system show -fields model')
    ssh_stdin_f, ssh_stdout_f, ssh_stderr_f = ssh.exec_command('system show -fields is-all-flash-optimized -node *')
    ssh_stdin_v, ssh_stdout_v, ssh_stderr_v = ssh.exec_command('version')
    
    k=0
    i=0
    j=0
    m=0
    f=0
    
    # Update the version
    for line in ssh_stdout:
        list_of_words = line.split()
        if(len(list_of_words) > 0):
            version[i.replace("##Looking for format which you want to search for ","").lower()]=list_of_words[2].replace(":","")

    #Cluster node and IP Information
    for line in ssh_stdout:
        test = line.strip('\n')
        list_of_words = test.split()

        i=i+1
        if(i==3):
            if(list_of_words[1]=="cluster_mgmt"):

                Server_Info.setdefault(list_of_words[0])
                Server_Info[list_of_words[0]] = list_of_words[2]

    #Node and Node IP Address
    for c in ssh_stdout_c:
        test = c.strip('\n')
        list_cluster = test.split()
        
        j=j+1
        if(j==5 or j==6 or j==7 or j==8):
            for text in list_cluster:
                if sub in text:
                    Cluster_Info[list_cluster[0].split('_mgmt1',1)[0]] = list_cluster[2].split('/',1)[0]
    
    #Service Processor IPv4 and IPv6
    for c in ssh_stdout_s:
        test = c.strip('\n')
        list_sp = test.split()
        
        k=k+1
        if(k==4 or k==6):
            if(list_sp[1]=="IPv4"):
                service_ps_ipv4.setdefault(list_sp[0])
                service_ps_ipv4[list_sp[0]] = list_sp[2]
        #Enable this section when IPv6 required for Service Processor
        '''
        if(k==5):
            if(list_sp[1]=="IPv6"):
                service_ps_ipv6.setdefault(list_sp[0])
                service_ps_ipv6[list_sp[0]] = list_sp[2]
        '''
    #Node and Model information    
    for line in ssh_stdout_m:
        test = line.strip('\n')
        list_model = test.split()        
        m=m+1
        for text in list_model:
            if model1 in text or model2 in text:
                modelinfo[list_model[0]] = list_model[1]
    for line in ssh_stdout_f:
        test = line.strip('\n')
        list_of_flash = test.split()
        #print(list_of_flash)
        f=f+1
        if(f==3 or f==4):
            if(list_of_flash):
                flash_Info.setdefault(list_of_flash[0])
                flash_Info[list_of_flash[0]] = list_of_flash[1]


    ssh.close()

# Test print statements
# print("Server Info \n",Server_Info)
# print("Cluster Info \n",Cluster_Info)
# print("Service Processor IPv4 Info \n",service_ps_ipv4)
# print("Service Processor IPv6 Info \n",service_ps_ipv6)
# print("Model Info \n",modelinfo)
# print("Flash Info \n",flash_Info)



db = MySQLdb.connect(host="#Database Connection", 
                     user="admin",
                     passwd="#Enter password",
                     db="#Database name")

cur = db.cursor()
up = db.cursor()
cur.execute("SELECT name, model, ipv4, isflash FROM nodes")


    

# # print all the first cell of all the rows
for row in cur.fetchall():
    for cluster,model,sp4,flash in zip(Cluster_Info,modelinfo,service_ps_ipv4,flash_Info):
        if(row[0].lower()==cluster and row[0].lower()==model and row[0].lower()==sp4 and row[0].lower()==flash ):
            
            cur.execute("UPDATE nodes SET ipv4 = %s WHERE name = %s",(Cluster_Info[cluster],cluster))
            db.commit()
            
            cur.execute("UPDATE nodes SET model = %s WHERE name = %s",(modelinfo[model],model))
            db.commit()
            
            up.execute("UPDATE nodes SET sp_ipv4 = %s WHERE name = %s",(service_ps_ipv4[sp4],sp4))
            db.commit()
            
            up.execute("UPDATE nodes SET isflash = %s WHERE name = %s",(flash_Info[flash],flash))
            db.commit()

cur.execute("SELECT name FROM table")
for row in cur.fetchall():
    for ver in version:
        if(row[0].lower()==ver):
            cur.execute("UPDATE systems SET version = %s WHERE name = %s",(version[ver],ver))
            db.commit()

db.close()
