#!/usr/bin/env python
import boto3
from datetime import datetime
import json
from bson import json_util
import os

import urllib3
urllib3.disable_warnings()
# boto3.set_stream_logger(name='botocore')

'''
conda install boto3 pymongo
'''

class awsrdsinventory():
    def __init__(self,symp,accesskey,secretkey):
        ## Define regions, I am using us-east-1 as sample
        region = "symphony"
        self.rdsinventory = []
        self.dbsubgrp = []
        self.url = "https://" + symp + "/api/v2/aws/rds"
        self.client = boto3.Session.client(boto3.session.Session(), service_name="rds",
                                           endpoint_url=self.url, region_name=region,
                                           aws_access_key_id=accesskey,
                                           aws_secret_access_key=secretkey, verify=False)


    def instancekey(self,inst,key):
        ## Module to handle potential unassigned value
        try:
            val=inst[key]
        except:
            val=""
        return val


    def updatedbjson(self,dbinstance):
        #print(dbinstance
        output={}
        output["MasterUsername"]=self.instancekey(dbinstance,"MasterUsername")
        output["MonitoringInterval"]=self.instancekey(dbinstance,"MonitoringInterval")
        output["LicenseModel"]=self.instancekey(dbinstance,"LicenseModel")
        output["InstanceCreateTime"]=self.instancekey(dbinstance,"InstanceCreateTime")
        output["AutoMinorVersionUpgrade"] =self.instancekey(dbinstance,"AutoMinorVersionUpgrade")
        output["PreferredBackupWindow"] =self.instancekey(dbinstance,"PreferredBackupWindow")
        output["AllocatedStorage"]=self.instancekey(dbinstance,"AllocatedStorage")
        output["DbiResourceId"]=self.instancekey(dbinstance,"DbiResourceId")
        output["VpcSecurityGroups"] =self.instancekey(dbinstance,"VpcSecurityGroups")
        output['DBName']=self.instancekey(dbinstance,'DBName')
        output["PreferredMaintenanceWindow"]=self.instancekey(dbinstance,"PreferredMaintenanceWindow")
        output['Port']=self.instancekey(dbinstance,'Endpoint')
        output["DBInstanceStatus"]=self.instancekey(dbinstance,"DBInstanceStatus")
        output["IAMDatabaseAuthenticationEnabled"] =self.instancekey(dbinstance,"IAMDatabaseAuthenticationEnabled")
        output["AvailabilityZone"]=self.instancekey(dbinstance,"AvailabilityZone")
        output["StorageEncrypted"]=self.instancekey(dbinstance,"StorageEncrypted")
        output["DBInstanceClass"]=self.instancekey(dbinstance,"DBInstanceClass")
        output["DbInstancePort"]=self.instancekey(dbinstance,"DbInstancePort")
        output["DBInstanceIdentifier"]=self.instancekey(dbinstance,"DBInstanceIdentifier")
        self.rdsinventory.append(output)


    def getrdsinfo(self):
        rds    = self.client.describe_db_instances()
        dbinstances=rds['DBInstances']
        for dbinstance in dbinstances:
            print(dbinstances)
            #print(dbinstance
            try:
                self.updatedbjson(dbinstance)
            except Exception as e:
                print("Failed to update info "+str(e.args)+e.message)
        self.rdsinventory=json.loads(json.dumps(self.rdsinventory,default=json_util.default))
        return self.rdsinventory

    def deletedb(self,dbidentifier):
        response = self.client.delete_db_instance(DBInstanceIdentifier=dbidentifier)
        return response

    def deletedbsubgrp(self):
        subgrps = self.client.describe_db_subnet_groups()
        subgrps = subgrps['DBSubnetGroups']
        for grp in subgrps:
            print(grp)
            self.client.delete_db_subnet_group(DBSubnetGroupName=grp['DBSubnetGroupName'])


class awslbinventory():
    def __init__(self,symp,accesskey,secretkey,vpcid):
    ## Define regions, I am using us-east-1 as sample
        region = "symphony"
        self.tgtgrpinventory = []
        self.lbinventory = []
        self.url = "https://" + symp + "/api/v2/aws/elb"
        self.vpcid = vpcid
        self.client = boto3.Session.client(boto3.session.Session(), service_name="elbv2",
                                           endpoint_url=self.url, region_name=region,
                                           aws_access_key_id=accesskey,
                                           aws_secret_access_key=secretkey, verify=False)

    def instancekey(self,inst,key):
        ## Module to handle potential unassigned value
        try:
            val=inst[key]
        except:
            val=""
        return val


    def updatelbjson(self,lb):
        if self.vpcid and self.instancekey(lb,'VpcId') != self.vpcid:
            return

        #print(dbinstance)
        output={}
        output["LoadBalancerArn"]=self.instancekey(lb,"LoadBalancerArn")
        output["VpcId"]=self.instancekey(lb,"VpcId")
        output["DNSName"]=self.instancekey(lb,"DNSName")
        output["CreatedTime"]=self.instancekey(lb,"CreatedTime")
        output["SecurityGroups"]=self.instancekey(lb,"SecurityGroups")
        self.lbinventory.append(output)

    def updatetgtjson(self,tgt):
        if self.vpcid and self.instancekey(tgt,'VpcId') != self.vpcid:
            return

        #print(dbinstance)
        output={}
        output["LoadBalancerArn"]=self.instancekey(tgt,"LoadBalancerArn")
        output["VpcId"]=self.instancekey(tgt,"VpcId")
        output["TargetGroupName"]=self.instancekey(tgt,"TargetGroupName")
        output["TargetGroupArn"]=self.instancekey(tgt,"TargetGroupArn")
        self.tgtgrpinventory.append(output)

    def getlbinfo(self):
        lbs    = self.client.describe_load_balancers()
        lbs = lbs['LoadBalancers']
        for lb in lbs:
            try:
                self.updatelbjson(lb)
            except Exception as e:
                print("Failed to update info " + str(e.args) + e.message)
        self.lbinventory=json.loads(json.dumps(self.lbinventory,default=json_util.default))
        return self.lbinventory

    def gettgtgrpinfo(self):
        tgts    = self.client.describe_target_groups()
        tgts = tgts['TargetGroups']
        for tgt in tgts:
            try:
                self.updatetgtjson(tgt)
            except Exception as e:
                print("Failed to update info " + str(e.args) + e.message)
        return self.tgtgrpinventory

    def deletelb(self,lbname):
        response = self.client.delete_load_balancer(LoadBalancerArn=lbname)
        return response

    def deletetgt(self,tgtarn):
        response = self.client.delete_target_group(TargetGroupArn=tgtarn)
        return response

class awsec2inventory():
    '''
       Class include modules to get inventory of EC2 instance for an aws ccount
       Script can be executed from ec2 or lambda with required role access

        When vpcid is set, only the resources that belong to the vpc are kept
    '''

    def __init__(self,symp,accesskey,secretkey,vpcid):
        ## Define regions, I am using us-east-1 as sample
        region = "symphony"
        self.inventory = []
        self.subnetinventory = []
        self.enisinventory = []
        self.secgrpinventory = []
        self.rtableinventory =[]
        self.vpcinventory = []
        self.url = "https://" + symp + "/api/v2/ec2/"
        self.vpcid = vpcid
        if vpcid:
            print("Will filter on " + vpcid)
        self.client = boto3.Session.client(boto3.session.Session(), service_name="ec2",
                                      endpoint_url=self.url, region_name=region,
                                      aws_access_key_id=accesskey,
                                      aws_secret_access_key=secretkey, verify=False)


    def instancekey(self, inst, key):
        ## Module to handle potential unassigned value
        try:
            val = inst[key]
        except:
            val = ""
        return val

    def updateec2json(self, inst, resid):
        if self.vpcid and inst['VpcId'] != self.vpcid:
            return

        output = {}
        output['ReservationId'] = resid
        output['Platform'] = self.instancekey(inst, 'Platform')
        output['PublicIpAddress'] = self.instancekey(inst, 'PublicIpAddress')
        output['InstanceType'] = self.instancekey(inst, 'InstanceType')
        output['AvailabilityZone'] = self.instancekey(inst, 'AvailabilityZone')
        output['ImageId'] = self.instancekey(inst, 'ImageId')
        output['Monitoring'] = inst['Monitoring']['State']
        output['PrivateIpAddress'] = inst['PrivateIpAddress']
        output['State'] = inst['State']['Name']
        output['LaunchTime'] = inst['LaunchTime']
        output['VpcId'] = inst['VpcId']
        output['InstanceId'] = inst['InstanceId']
        try:
            output['tag'] = [tag['Value'] for tag in inst['Tags']]
        except:
            output['tag'] = ""
        secgroups = ""
        if output['State'] == 'running':
            securityGroups = inst['SecurityGroups']
            secgroups = [secgroups['GroupName'] for secgroups in securityGroups]
            output['SecurityGroups'] = secgroups
        self.inventory.append(output)

    def updatesubnetjson(self, subnet):
        if self.vpcid and self.instancekey(subnet,'VpcId') != self.vpcid:
            return

        output = {}
        output['SubnetId'] = self.instancekey(subnet,'SubnetId')
        output['CidrBlock'] = self.instancekey(subnet,'CidrBlock')
        output['VpcId'] = self.instancekey(subnet,'VpcId')
        self.subnetinventory.append(output)

    def updateenijson(self, eni):
        if self.vpcid and self.instancekey(eni,'VpcId') != self.vpcid:
            return

        output = {}
        output['NetworkInterfaceId'] = self.instancekey(eni,'NetworkInterfaceId')
        output['PrivateIpAddress'] = eni.get('PrivateIpAddresses', [{'PrivateIpAddress':''}])[0]['PrivateIpAddress']
        output['VpcId'] = self.instancekey(eni,'VpcId')
        self.enisinventory.append(output)

    def updatesecgrpjson(self, secgrp):
        if self.vpcid and self.instancekey(secgrp,'VpcId') != self.vpcid:
            return

        output = {}
        output['GroupId'] = self.instancekey(secgrp,'GroupId')
        output['IpPermissionsEgress'] = self.instancekey(secgrp,'IpPermissionsEgress')
        output['Description']=self.instancekey(secgrp,'Description')
        output['IpPermissions']=self.instancekey(secgrp,'IpPermissions')
        output['VpcId'] = self.instancekey(secgrp,'VpcId')
        output['OwnerId'] = self.instancekey(secgrp,'OwnerId')
        self.secgrpinventory.append(output)

    def updatevpcjson(self, vpc):
        if self.vpcid and self.instancekey(vpc,'VpcId') != self.vpcid:
            return

        output = {}
        output['VpcId'] = self.instancekey(vpc,'VpcId')
        output['Tags'] = self.instancekey(vpc,'Tags')
        output['State']=self.instancekey(vpc,'State')
        output['CidrBlock']=self.instancekey(vpc,'CidrBlock')
        output['IsDefault'] = self.instancekey(vpc,'IsDefault')
        output['InstanceTenancy'] = self.instancekey(vpc,'InstanceTenancy')
        self.vpcinventory.append(output)

    def updatertablejson(self, rtable):
        if self.vpcid and self.instancekey(rtable,'VpcId') != self.vpcid:
            return

        output = {}
        output['RouteTableId'] = self.instancekey(rtable,'RouteTableId')
        output['Main'] = self.instancekey(rtable,'Main')
        output['State']=self.instancekey(rtable,'State')
        output['Tags']=self.instancekey(rtable,'Tags')
        output['VpcId'] = self.instancekey(rtable,'VpcId')
        self.rtableinventory.append(output)

    def getinstanceinfo(self):
        ecinventory = self.client.describe_instances()
        reservations = ecinventory.get('Reservations', [])
        for reservation in reservations:
            resid = reservation['ReservationId']
            instances = [i for i in reservation['Instances']]
            for inst in instances:
                try:
                    self.updateec2json(inst, resid)
                except Exception as e:
                    print("Failed to update info " + str(e.args) + e.message)

        self.inventory=json.loads(json.dumps(self.inventory,default=json_util.default))
        for i in self.inventory:
            print("============================")
            print(i)
        return self.inventory

    def getenisinfo(self):
        enisinventory = self.client.describe_network_interfaces()
        enis = enisinventory.get('NetworkInterfaces', [])
        for eni in enis:
            print(eni)
            try:
                self.updateenijson(eni)
            except Exception as e:
                print("Failed to update info " + str(e.args) + e.message)
        self.enisinventory = json.loads(json.dumps(self.enisinventory, default=json_util.default))
        for i in self.enisinventory:
            print("============================")
            print(i)
        return self.enisinventory

    def getsubnetsinfo(self):
        subnetinventory=self.client.describe_subnets()
        subnets=subnetinventory['Subnets']
        for subnet in subnets:
            print(subnet)
            try:
                self.updatesubnetjson(subnet)
            except Exception as e:
                print("Failed to update info " + str(e.args) + e.message)
        self.subnetinventory=json.loads(json.dumps(self.subnetinventory,default=json_util.default))
        for i in self.subnetinventory:
            print("============================")
            print(i)
        return self.subnetinventory

    def getsecuritygrpinfo(self):
        secgrpinventory=self.client.describe_security_groups()
        secgrps=secgrpinventory['SecurityGroups']
        for secgrp in secgrps:
            try:
                self.updatesecgrpjson(secgrp)
            except Exception as e:
                print("Failed to update info " + str(e.args) + e.message)
        self.secgrpinventory=json.loads(json.dumps(self.secgrpinventory,default=json_util.default))
        for i in self.secgrpinventory:
            print("============================")
            print(i)
        return self.secgrpinventory

    def getrouteinfo(self):
        rtableinventory=self.client.describe_route_tables()
        rtables=rtableinventory['RouteTables']
        for rtable in rtables:
            try:
                self.updatertablejson(rtable)
            except Exception as e:
                print("Failed to update info " + str(e.args) + e.message)
        self.rtableinventory=json.loads(json.dumps(self.rtableinventory,default=json_util.default))
        for i in self.rtableinventory:
            print("============================")
            print(i)
        return self.rtableinventory

    def getvpcinfo(self):
        vpcinventory=self.client.describe_vpcs()
        vpcs=vpcinventory['Vpcs']
        for vpc in vpcs:
            print(vpc)
            try:
                self.updatevpcjson(vpc)
            except Exception as e:
                print("Failed to update info " + str(e.args) + e.message)
        self.vpcinventory=json.loads(json.dumps(self.vpcinventory,default=json_util.default))
        for i in self.vpcinventory:
            print(".============================")
            print(i)
        return self.vpcinventory

    def deleteinstance(self,instanceId):
        response=self.client.terminate_instances(InstanceIds=[instanceId])
        return response

    def deleteeni(self,networkInterfaceId):
        response=self.client.delete_network_interface(NetworkInterfaceId=networkInterfaceId)

        return response

    def deletesubnet(self,subnetId):
        response=self.client.delete_subnet(SubnetId=subnetId)
        return response

    def deletesecgrp(self,secgrpId):
        response=self.client.delete_security_group(GroupId=secgrpId)
        return response

    def deletertable(self,rtableId):
        response=self.client.delete_route_table(RouteTableId=rtableId)
        return response

    def deletedhcpoptions(self):
        dhcps = self.client.describe_dhcp_options()
        # print(dhcps)
        dhcps = dhcps['DhcpOptions']
        print("dhcps['DhcpOptions']")
        print(dhcps)
        for dhcp in dhcps:
            # if self.vpcid and dhcp['VpcId'] != self.vpcid:
            #     continue
            # print("Deleting " + str(dhcp))
            response = self.client.delete_dhcp_options(DhcpOptionsId=dhcp['DhcpOptionsId'])
        return response

    def deletevpc(self,VpcId):
        response=self.client.delete_vpc(VpcId=VpcId)
        return response

def handlebotoerror(id, e):
    print("Error deleting "+id)
    if hasattr(e, 'message') and hasattr(e, 'args'):
        print("error:"+str(e.args)+str(e.message))
    elif hasattr(e, 'message'):
        print("error:"+str(e.message))
    else:
        print("error:", str(e))

    if hasattr(e, 'response'):
        print("Detailed error: ", e.response)
    
    # raise e

## Sample execution - TODO: a CLI.
region = os.environ['STRATO_CLUSTER']
accesskey = os.environ['AWS_ACCESS_KEY_ID']
secretkey = os.environ['AWS_SECRET_ACCESS_KEY']
vpcid = os.environ['VPCID']
if vpcid ==  'NA' or vpcid ==  'na':
    vpcid = None
eradicate = os.getenv('ERADICATE', None)

a = awsec2inventory(region,accesskey,secretkey,vpcid)
instances=a.getinstanceinfo()
enis=a.getenisinfo()
subnets=a.getsubnetsinfo()
secgrps=a.getsecuritygrpinfo()
print("=========#############********&&&&&&&&&&&")
print("Instances:")
print(instances)
print("Vpc-Info")
vpcs=a.getvpcinfo()
print("Route Info")
rtables=a.getrouteinfo()
print("LB Inventory")
lbaas = awslbinventory(region,accesskey,secretkey,vpcid)
print("LB Info")
lbs=lbaas.getlbinfo()
print("RDS Inventory")
rds=awsrdsinventory(region,accesskey,secretkey)
print("RDS Info")
dbs=rds.getrdsinfo()
print("GRP Info")
tgts=lbaas.gettgtgrpinfo()
if eradicate:
    print("===============================")
    print("========= Eradicating =========")
    for instance in instances:
        try:
            print(a.deleteinstance(instance['InstanceId']))
        except Exception as e:
            handlebotoerror(instance['InstanceId'], e)

    for eni in enis:
        try:
            print(a.deleteeni(eni['NetworkInterfaceId']))
        except Exception as e:
            handlebotoerror(eni['VpcId'] + "-" + eni['NetworkInterfaceId'], e)

    for subnet in subnets:
        try:
            print(a.deletesubnet(subnet['SubnetId']))
        except Exception as e:
            handlebotoerror(subnet['VpcId'] + "-" + subnet['SubnetId'], e)

    for secgrp in secgrps:
        try:
            print(a.deletesecgrp(secgrp['GroupId']))
        except Exception as e:
            handlebotoerror(secgrp['GroupId'], e)

    for rtable in rtables:
        try:
            print(a.deletertable(rtable['RouteTableId']))
        except Exception as e:
            handlebotoerror(rtable['RouteTableId'], e)

    for lb in lbs:
        try:
            print(lbaas.deletelb(lb['LoadBalancerArn']))
        except Exception as e:
            handlebotoerror(lb['LoadBalancerArn'], e)

    for db in dbs:
        try:
            print(rds.deletedb(db['DBInstanceIdentifier']))
        except Exception as e:
            handlebotoerror(db['DBInstanceIdentifier'], e)
    rds.deletedbsubgrp()
    for tgt in tgts:
        try:
            print(lbaas.deletetgt(tgt['TargetGroupArn']))
        except Exception as e:
            handlebotoerror(tgt['TargetGroupArn'], e)

    for vpc in vpcs:
        try:
            if not vpc['IsDefault']:
                print("DELETING VPC")
                print(a.deletevpc(vpc['VpcId']))
        except Exception as e:
            handlebotoerror(vpc['VpcId'], e)

# a.deletedhcpoptions()

