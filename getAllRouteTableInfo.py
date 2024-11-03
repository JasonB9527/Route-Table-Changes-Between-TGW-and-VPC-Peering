import boto3
import csv

def get_route_tables_for_vpc(session, vpc_id):
    ec2 = session.client('ec2')
    response = ec2.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    return response['RouteTables']

def find_routes(session, vpc_id, destination_cidrs):
    routes_info = []
    route_tables = get_route_tables_for_vpc(session, vpc_id)
    
    for rt in route_tables:
        rt_id = rt['RouteTableId']
        for route in rt['Routes']:
            if route.get('DestinationCidrBlock') in destination_cidrs:
                gateway = None
                if 'GatewayId' in route:
                    gateway = route['GatewayId']
                elif 'NatGatewayId' in route:
                    gateway = route['NatGatewayId']
                elif 'VpcPeeringConnectionId' in route:
                    gateway = route['VpcPeeringConnectionId']
                elif 'TransitGatewayId' in route:
                    gateway = route['TransitGatewayId']
                elif 'InstanceId' in route:
                    gateway = route['InstanceId']
                
                routes_info.append([vpc_id, rt_id, route.get('DestinationCidrBlock'), gateway])
    
    return routes_info


# Account A credentials
account1_access_key = 'your_account1_access_key'
account1_secret_key = 'your_account1_secret_key'
account1_region = 'your_account1_region'

# Account B credentials
account2_access_key = 'your_account2_access_key'
account2_secret_key = 'your_account2_secret_key'
account2_region = 'your_account2_region'

# Create sessions for both accounts
session_a = boto3.Session(
    aws_access_key_id=account1_access_key,
    aws_secret_access_key=account1_secret_key,
    region_name=account1_region
)

session_b = boto3.Session(
    aws_access_key_id=account2_access_key,
    aws_secret_access_key=account2_secret_key,
    region_name=account2_region
)

# VPC and route details
vpc_id_a = 'your_account1_vpc-id'
vpc_id_b = 'your_account2_vpc-id'
destination_cidr_blocks_a = ['172.17.0.0/16', '10.0.0.0/8']  # your cidr
destination_cidr_blocks_b = ['172.16.0.0/16', '192.168.0.0/16']  # supoprt multi-cidr

# Get route information
routes_a = find_routes(session_a, vpc_id_a, destination_cidr_blocks_a)
routes_b = find_routes(session_b, vpc_id_b, destination_cidr_blocks_b)

# Combine results
all_routes = routes_a + routes_b

# Write to CSV
with open('route_info.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['vpc', 'route table id', 'dest vpc cidr', 'gateway'])
    writer.writerows(all_routes)

print("CSV file 'route_info.csv' has been created with the route information.")