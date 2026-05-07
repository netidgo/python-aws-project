import boto3
client = boto3.client('ec2')
elbv2 = boto3.client('elbv2')

# 키페어 생성
def create_key_pair(pjt_name):
    key_pair = client.create_key_pair(
    KeyName=f'{pjt_name}-key',
    KeyType='rsa',
    TagSpecifications=[
        {
            'ResourceType': 'key-pair',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': f'{pjt_name}-key'
                },
            ]
        },
    ],
    KeyFormat='ppk',
    )
    key = open(f'{pjt_name}-key.ppk','w')
    key.write(key_pair['KeyMaterial'])
    key.close()
    key_name = key_pair['KeyName']
    return key_name

# 보안그룹 생성 - 베스천호스트용
def create_security_group_bastion(pjt_name,vpc_id):
    security_group_bastion = client.create_security_group(
    Description=f'{pjt_name}-bastion-sg',
    GroupName=f'{pjt_name}-bastion-sg',
    VpcId=vpc_id,
    TagSpecifications=[
        {
            'ResourceType': 'security-group',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': f'{pjt_name}-bastion-sg'
                },
            ]
        },
    ],
    )
    client.authorize_security_group_ingress(
    GroupId=security_group_bastion['GroupId'],
    IpPermissions=[
        {
            'IpProtocol': 'tcp',
            'FromPort': 22,
            'ToPort': 22,
            'IpRanges': [
                {
                    'Description': 'Allow SSH',
                    'CidrIp': '0.0.0.0/0'
                },
            ],
        },
    ],
    )
    sg_bastion_id = security_group_bastion['GroupId']
    return sg_bastion_id

# 보안그룹 생성 - ALB용
def create_security_group_alb(pjt_name,vpc_id):
    security_group_alb = client.create_security_group(
    Description=f'{pjt_name}-alb-sg',
    GroupName=f'{pjt_name}-alb-sg',
    VpcId=vpc_id,
    TagSpecifications=[
        {
            'ResourceType': 'security-group',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': f'{pjt_name}-alb-sg'
                },
            ]
        },
    ],
    )
    client.authorize_security_group_ingress(
    GroupId=security_group_alb['GroupId'],
    IpPermissions=[
        {
            'IpProtocol': 'tcp',
            'FromPort': 80,
            'ToPort': 80,
            'IpRanges': [
                {
                    'Description': 'Allow HTTP',
                    'CidrIp': '0.0.0.0/0'
                },
            ],
        },
        {
            'IpProtocol': 'tcp',
            'FromPort': 443,
            'ToPort': 443,
            'IpRanges': [
                {
                    'Description': 'Allow HTTPS',
                    'CidrIp': '0.0.0.0/0'
                },
            ],
        },
    ],
    )
    sg_alb_id = security_group_alb['GroupId']
    return sg_alb_id

# 보안그룹 생성 - WEB 서버용
def create_security_group_web(pjt_name,vpc_id,sg_bastion_id,sg_alb_id):
    security_group_web = client.create_security_group(
    Description=f'{pjt_name}-web-sg',
    GroupName=f'{pjt_name}-web-sg',
    VpcId=vpc_id,
    TagSpecifications=[
        {
            'ResourceType': 'security-group',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': f'{pjt_name}-web-sg'
                },
            ]
        },
    ],
    )
    client.authorize_security_group_ingress(
    GroupId=security_group_web['GroupId'],
    IpPermissions=[
        {
            'IpProtocol': 'tcp',
            'FromPort': 22,
            'ToPort': 22,
            'UserIdGroupPairs': [
                {
                    'Description': 'Allow SSH',
                    'GroupId': sg_bastion_id,
                },
            ],
        },
        {
            'IpProtocol': 'tcp',
            'FromPort': 80,
            'ToPort': 80,
            'UserIdGroupPairs': [
                {
                    'Description': 'Allow SSH',
                    'GroupId': sg_alb_id,
                },
            ],
        },
    ],
    )
    sg_web_id = security_group_web['GroupId']
    return sg_web_id

# 베스천 호스트 생성
def create_ec2_bastion(pjt_name,ami,key_name,sg_bastion_id,pub_sn2_id):
    bastion = client.run_instances(
    ImageId=ami,
    InstanceType='t3.micro',
    KeyName=key_name,
    MaxCount=1,
    MinCount=1,
    NetworkInterfaces=[
        {
            'AssociatePublicIpAddress': True,
            'DeviceIndex': 0,
            'Groups': [
                sg_bastion_id,
            ],
            'SubnetId': pub_sn2_id,
        }
    ],
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': f'{pjt_name}-bastion',
                },
            ],
        },
    ],
    )
    bastion_id = bastion['Instances'][0]['InstanceId']
    return bastion_id

# 웹서버 1 생성
def create_ec2_web1(pjt_name,ami,key_name,sg_web_id,pri_sn3_id,web1_user_data):
    web1 = client.run_instances(
    ImageId=ami,
    InstanceType='t3.micro',
    KeyName=key_name,
    MaxCount=1,
    MinCount=1,
    UserData=web1_user_data,
    NetworkInterfaces=[
        {
            'AssociatePublicIpAddress': False,
            'DeviceIndex': 0,
            'Groups': [
                sg_web_id,
            ],
            'SubnetId': pri_sn3_id,
        }
    ],
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': f'{pjt_name}-web1',
                },
            ],
        },
    ],
    )
    web1_id = web1['Instances'][0]['InstanceId']
    waiter = client.get_waiter('instance_running')
    waiter.wait(InstanceIds=[web1_id])
    return web1_id

# 웹서버 2 생성
def create_ec2_web2(pjt_name,ami,key_name,sg_web_id,pri_sn4_id,web2_user_data):
    web2 = client.run_instances(
    ImageId=ami,
    InstanceType='t3.micro',
    KeyName=key_name,
    MaxCount=1,
    MinCount=1,
    UserData=web2_user_data,
    NetworkInterfaces=[
        {
            'AssociatePublicIpAddress': False,
            'DeviceIndex': 0,
            'Groups': [
                sg_web_id,
            ],
            'SubnetId': pri_sn4_id,
        }
    ],
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': f'{pjt_name}-web2',
                },
            ],
        },
    ],
    )
    web2_id = web2['Instances'][0]['InstanceId']
    waiter = client.get_waiter('instance_running')
    waiter.wait(InstanceIds=[web2_id])
    return web2_id

# 어플리케이션 로드밸런서 생성
def create_alb_web(pjt_name,pub_sn_ids,sg_alb_ids,vpc_id,web1_id,web2_id):
    alb_web = elbv2.create_load_balancer(
    Name=f'{pjt_name}-alb-web',
    Subnets=pub_sn_ids,
    SecurityGroups=sg_alb_ids,
    Scheme='internet-facing',
    Tags=[
        {
            'Key': 'Name',
            'Value': f'{pjt_name}-alb-web'
        },
    ],
    Type='application',
    IpAddressType='ipv4',
    )
    tg_web = elbv2.create_target_group(
    Name=f'{pjt_name}-tg-web',
    Protocol='HTTP',
    Port=80,
    VpcId=vpc_id,
    HealthCheckProtocol='HTTP',
    HealthCheckPort='80',
    HealthCheckEnabled=True,
    HealthCheckPath='/',
    HealthCheckIntervalSeconds=10,
    HealthCheckTimeoutSeconds=3,
    HealthyThresholdCount=3,
    UnhealthyThresholdCount=3,
    TargetType='instance',
    Tags=[
        {
            'Key': 'Name',
            'Value': f'{pjt_name}-tg-web'
        },
    ],
    IpAddressType='ipv4',
    )
    register_web = elbv2.register_targets(
    TargetGroupArn=tg_web['TargetGroups'][0]['TargetGroupArn'],
    Targets=[
        {
            'Id': web1_id,
            'Port': 80,
        },
        {
            'Id': web2_id,
            'Port': 80,
        },
    ]
    )
    listener_web = elbv2.create_listener(
    DefaultActions=[
        {
            'TargetGroupArn': tg_web['TargetGroups'][0]['TargetGroupArn'],
            'Type': 'forward',
        },
    ],
    LoadBalancerArn=alb_web['LoadBalancers'][0]['LoadBalancerArn'],
    Port=80,
    Protocol='HTTP',
    )
    alb_arn = alb_web['LoadBalancers'][0]['LoadBalancerArn']
    tg_arn = tg_web['TargetGroups'][0]['TargetGroupArn']
    return alb_arn, tg_arn