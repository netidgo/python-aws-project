import create_vpc_layer as cvpc
import create_ec2_layer as cec2

pjt_name = input('프로젝트 이름은?[seoul] ' ) or 'seoul'
vpc_cidr = input('VPC CIDR은?[172.16.0.0/16] ')  or '172.16.0.0/16'
region = input('리전 이름은?[ap-northeast-2] ') or 'ap-northeast-2'
ami = input('인스턴스 AMI?[ami-0d4c056a16f3ae150] ') or 'ami-0d4c056a16f3ae150'

# VPC Layer 생성
print('===================================')
print('이 프로젝트의 VPC 자원 생성을 시작합니다.')
vpc1 = cvpc.create_vpc(pjt_name,vpc_cidr)
print(f'VPC ID: {vpc1[0]}')
print(f'IGW ID: {vpc1[1]}')

sn_cidr = vpc_cidr.split('.')
pub_sn1 = cvpc.create_subnet(pjt_name,f'{sn_cidr[0]}.{sn_cidr[1]}.1.0/24',vpc1[0],f'{region}a')
pub_sn2 = cvpc.create_subnet(pjt_name,f'{sn_cidr[0]}.{sn_cidr[1]}.2.0/24',vpc1[0],f'{region}c')
pri_sn3 = cvpc.create_subnet(pjt_name,f'{sn_cidr[0]}.{sn_cidr[1]}.3.0/24',vpc1[0],f'{region}a')
pri_sn4 = cvpc.create_subnet(pjt_name,f'{sn_cidr[0]}.{sn_cidr[1]}.4.0/24',vpc1[0],f'{region}c')
print(f'Pubic Sunbet1 ID: {pub_sn1}')
print(f'Pubic Sunbet2 ID: {pub_sn2}')
print(f'Private Sunbet3 ID: {pri_sn3}')
print(f'Private Sunbet4 ID: {pri_sn4}')

nat_gw1 = cvpc.create_nat_gw(pjt_name,pub_sn1)
print(f'Nat Gateway ID: {nat_gw1}')

pub_rt12 = cvpc.create_pub_rt(pjt_name,vpc1[0],pub_sn1,pub_sn2,vpc1[1])
print(f'Public Route Table ID: {pub_rt12}')
pri_rt34 = cvpc.create_pri_rt(pjt_name,vpc1[0],pri_sn3,pri_sn4,nat_gw1)
print(f'Pravate Route Table ID: {pri_rt34}')

print('이 프로젝트의 VPC 자원을 모두 생성하였습니다.')
print('===================================')

# EC2 Layer 생성
print('===================================')
print('이 프로젝트의 EC2 자원 생성을 시작합니다.')
key_pair1 = cec2.create_key_pair(pjt_name)
print(key_pair1)

sg_bastion = cec2.create_security_group_bastion(pjt_name,vpc1[0])
print(sg_bastion)
sg_alb = cec2.create_security_group_alb(pjt_name,vpc1[0])
print(sg_alb)
sg_web = cec2.create_security_group_web(pjt_name,vpc1[0],sg_bastion,sg_alb)
print(sg_web)

ec2_bastion = cec2.create_ec2_bastion(pjt_name,ami,key_pair1,sg_bastion,pub_sn2)
print(ec2_bastion)
web1_user_data = '''\
#!/bin/bash
yum install -y httpd
systemctl start httpd
systemctl enable httpd
echo "<h1>AWS SDK for Python Web Server 1</h1>" > /var/www/html/index.html
'''
ec2_web1 = cec2.create_ec2_web1(pjt_name,ami,key_pair1,sg_web,pri_sn3,web1_user_data)
print(ec2_web1)
web2_user_data = '''\
#!/bin/bash
yum install -y httpd
systemctl start httpd
systemctl enable httpd
echo "<h1>AWS SDK for Python Web Server 2</h1>" > /var/www/html/index.html
'''
ec2_web2 = cec2.create_ec2_web2(pjt_name,ami,key_pair1,sg_web,pri_sn4,web2_user_data)
print(ec2_web2)

alb_web = cec2.create_alb_web(pjt_name,[pub_sn1,pub_sn2],[sg_alb],vpc1[0],ec2_web1,ec2_web2)
print(alb_web[0])
print(alb_web[1])
print('===================================')
print('이 프로젝트의 EC2 자원을 모두 생성하였습니다.')