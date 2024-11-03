import boto3
import concurrent.futures

def replace_route(session, route_table_id, destination_cidr_block, transit_gateway_id):
    ec2 = session.client('ec2')
    try:
        response = ec2.replace_route(
            RouteTableId=route_table_id,
            DestinationCidrBlock=destination_cidr_block,
            TransitGatewayId=transit_gateway_id
        )
        print(f"Route replaced successfully in route table {route_table_id} for CIDR {destination_cidr_block}")
        return response
    except Exception as e:
        print(f"Error replacing route in {route_table_id} for CIDR {destination_cidr_block}: {str(e)}")
        return None

def get_route_tables_for_vpc(session, vpc_id):
    ec2 = session.client('ec2')
    response = ec2.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    return response['RouteTables']

def process_route_table(session, route_table, destination_cidr_blocks, transit_gateway_id):
    route_table_id = route_table['RouteTableId']
    results = []
    for destination_cidr_block in destination_cidr_blocks:
        for route in route_table['Routes']:
            if route.get('DestinationCidrBlock') == destination_cidr_block:
                result = replace_route(session, route_table_id, destination_cidr_block, transit_gateway_id)
                results.append(result)
                break
        else:
            print(f"No matching route found in route table {route_table_id} for CIDR {destination_cidr_block}")
    return results

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
destination_cidr_blocks_a = ['172.17.0.0/16', '10.0.0.0/8']  # 支持多个CIDR
destination_cidr_blocks_b = ['172.16.0.0/16', '192.168.0.0/16']  # 支持多个CIDR
transit_gateway_id = 'tgw-xxxxxxxxxxxxxxxxxx'

# Get all route tables for the specified VPCs
route_tables_a = get_route_tables_for_vpc(session_a, vpc_id_a)
route_tables_b = get_route_tables_for_vpc(session_b, vpc_id_b)

# Create a list of tasks
tasks = []
for route_table in route_tables_a:
    tasks.append((session_a, route_table, destination_cidr_blocks_a, transit_gateway_id))
for route_table in route_tables_b:
    tasks.append((session_b, route_table, destination_cidr_blocks_b, transit_gateway_id))

# Use ThreadPoolExecutor to run tasks in parallel
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
    # Submit tasks
    future_to_task = {executor.submit(process_route_table, *task): task for task in tasks}
    
    # Wait for all tasks to complete
    for future in concurrent.futures.as_completed(future_to_task):
        task = future_to_task[future]
        try:
            results = future.result()
            if results:
                print(f"Task completed for route table {task[1]['RouteTableId']}")
        except Exception as exc:
            print(f"Task for route table {task[1]['RouteTableId']} generated an exception: {exc}")

print("All tasks completed.")