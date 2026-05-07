import boto3
client = boto3.client('ec2')

# VPC와 IGW 생성
def create_vpc(pjt_name, vpc_cidr):
    vpc = client.create_vpc(
    CidrBlock=vpc_cidr,
    TagSpecifications=[
        {
            'ResourceType': 'vpc',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': f'{pjt_name}-vpc'
                },
            ]
        },
    ],
    )
    vpc_id = vpc['Vpc']['VpcId']
    igw = client.create_internet_gateway(
    TagSpecifications=[
        {
            'ResourceType': 'internet-gateway',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': f'{pjt_name}-igw'
                },
            ]
        },
    ],
    )
    igw_id = igw['InternetGateway']['InternetGatewayId']
    client.attach_internet_gateway(
    InternetGatewayId=igw_id,
    VpcId=vpc_id
    )
    return vpc_id, igw_id

# 서브넷 생성
def create_subnet(pjt_name,sn_cidr,vpc_id,az_name):
    subnet = client.create_subnet(
    TagSpecifications=[
        {
            'ResourceType': 'subnet',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': f'{pjt_name}-{sn_cidr}-sn'
                },
            ]
        },
    ],
    AvailabilityZone=az_name,
    CidrBlock=sn_cidr,
    VpcId=vpc_id,
    )
    subnet_id = subnet['Subnet']['SubnetId']
    return subnet_id

# 탄력적 IP & NAT 게이트웨이 생성
def create_nat_gw(pjt_name,subnet_id):
    eip = client.allocate_address(
    Domain='vpc',
    TagSpecifications=[
        {
            'ResourceType': 'elastic-ip',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': f'{pjt_name}-nat-eip'
                },
            ]
        },
    ],
    )
    nat_gw = client.create_nat_gateway(
    AllocationId=eip['AllocationId'],
    SubnetId=subnet_id,
    TagSpecifications=[
        {
            'ResourceType': 'natgateway',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': f'{pjt_name}-nat-gw'
                },
            ]
        },
    ],
    )
    nat_gw_id = nat_gw['NatGateway']['NatGatewayId']
    waiter = client.get_waiter('nat_gateway_available')
    waiter.wait(NatGatewayIds=[nat_gw_id])
    return nat_gw_id

# 퍼블릭 라우팅 테이블 생성 및 기본 경로
def create_pub_rt(pjt_name,vpc_id,subnet1_id,subnet2_id,igw_id):
    pub_route_table = client.create_route_table(
    TagSpecifications=[
        {
            'ResourceType': 'route-table',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': f'{pjt_name}-pub-rt'
                },
            ]
        },
    ],
    VpcId=vpc_id
    )
    ass_pub_sn1 = client.associate_route_table(
    SubnetId=subnet1_id,
    RouteTableId=pub_route_table['RouteTable']['RouteTableId']
    )
    ass_pub_sn2 = client.associate_route_table(
    SubnetId=subnet2_id,
    RouteTableId=pub_route_table['RouteTable']['RouteTableId']
    )
    default_route = client.create_route(
    RouteTableId=pub_route_table['RouteTable']['RouteTableId'],
    DestinationCidrBlock='0.0.0.0/0',
    GatewayId=igw_id,
    )
    route_table_id = pub_route_table['RouteTable']['RouteTableId']
    return route_table_id

# 프라이빗 라우팅 테이블 생성 및 기본 경로
def create_pri_rt(pjt_name,vpc_id,subnet3_id,subnet4_id,nat_id):
    pri_route_table = client.create_route_table(
    TagSpecifications=[
        {
            'ResourceType': 'route-table',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': f'{pjt_name}-pri-rt'
                },
            ]
        },
    ],
    VpcId=vpc_id
    )
    ass_pri_sn3 = client.associate_route_table(
    SubnetId=subnet3_id,
    RouteTableId=pri_route_table['RouteTable']['RouteTableId']
    )
    ass_pri_sn4 = client.associate_route_table(
    SubnetId=subnet4_id,
    RouteTableId=pri_route_table['RouteTable']['RouteTableId']
    )
    default_route = client.create_route(
    RouteTableId=pri_route_table['RouteTable']['RouteTableId'],
    DestinationCidrBlock='0.0.0.0/0',
    NatGatewayId=nat_id,
    )
    route_table_id = pri_route_table['RouteTable']['RouteTableId']
    return route_table_id