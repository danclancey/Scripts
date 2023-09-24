"""
---------------------------------------------------------------
Script Name: CDP Neighbor Info Fetcher via Telnet and Parser
Author: Dan Clancey
Date: 2-May-2023
Version: 1.0
Description:
    This script connects to a remote device via Telnet to retrieve CDP (Cisco Discovery Protocol) neighbor information.
    The raw CDP neighbor information is saved to a specified text file. The script then parses this information to collect
    relevant details like Device ID, IP address, Platform, Capabilities, and Interface. The parsed information is
    then written to a CSV file for easy analysis.

Usage:
    python cdp_neighbor_telnet.py -u [TELNET_USERNAME] -p [TELNET_PASSWORD] -H [TELNET_HOST] -t [TEXT_OUTPUT_FILE]

    Where:
    [TELNET_USERNAME] is the Telnet username for the device.
    [TELNET_PASSWORD] is the Telnet password for the device.
    [TELNET_HOST] is the Telnet hostname or IP address of the device.
    [TEXT_OUTPUT_FILE] is the output text file to store raw CDP neighbor information.

Examples:
    python cdp_neighbor_telnet.py -u admin -p password -H 192.168.1.1 -t cdp_output.txt

Requirements:
    - Python 3.x
    - telnetlib library for Telnet
    - argparse library for parsing command-line arguments
    - re library for regular expression matching
    - csv library for CSV file operations
    - os library for file and path manipulation
---------------------------------------------------------------
"""

import re
import csv
import argparse
import telnetlib
import os

def telnet_and_save_cdp_neighbors(username, password, host, output_file):
    telnet = telnetlib.Telnet(host)
    telnet.read_until(b'Username:')
    telnet.write(username.encode('ascii') + b'\n')

    if password:
        telnet.read_until(b'Password:')
        telnet.write(password.encode('ascii') + b'\n')

    telnet.write(b'terminal length 0\n')  # To avoid pagination in the output
    telnet.write(b'show cdp neighbors detail\n')
    telnet.write(b'exit\n')

    cdp_neighbors_output = telnet.read_until(b'exit').decode()  # Read data until the 'exit' string is encountered

    with open(output_file, 'w') as file:
        file.write(cdp_neighbors_output)

    telnet.close()

def parse_cdp_neighbors(data):
    neighbors = []

    device_id_pattern = re.compile(r'Device ID:(.+)')
    ip_address_pattern = re.compile(r'IPv4 Address: (.+)|IP address: (.+)')
    platform_pattern = re.compile(r'Platform: (.+),\s*Capabilities: (.+)')
    interface_pattern = re.compile(r'Interface: (.+),\s*Port ID \(outgoing port\): (.+)|Interface: (.+),\s*Port ID \(outgoing port\): (.+)')
    management_address_pattern = re.compile(r'Management address\(es\):')

    lines = data.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1

        if device_id_pattern.match(line):
            neighbor = {}
            neighbor['device_id'] = device_id_pattern.match(line).group(1).strip()

            while i < len(lines):
                line = lines[i].strip()
                i += 1

                if ip_address_pattern.match(line):
                    match = ip_address_pattern.match(line)
                    neighbor['ip_address'] = match.group(1).strip() if match.group(1) else match.group(2).strip()
                elif platform_pattern.match(line):
                    neighbor['platform'], neighbor['capabilities'] = platform_pattern.match(line).group(1, 2)
                elif interface_pattern.match(line):
                    match = interface_pattern.match(line)
                    neighbor['interface'] = match.group(1).strip() if match.group(1) else match.group(3).strip()
                elif management_address_pattern.match(line):
                    while i < len(lines) and not re.match(r'\S', lines[i]):
                        i += 1
                    line = lines[i].strip()
                    ip_address = re.match(r'IP address: (.+)|IPv4 Address: (.+)', line)
                    if ip_address:
                        neighbor['management_address'] = ip_address.group(1).strip() if ip_address.group(1) else ip_address.group(2).strip()
                elif '---' in line:
                    neighbors.append(neighbor)
                    break
            else:
                neighbors.append(neighbor)  # Append the last neighbor when the loop finishes

    return neighbors


# Parse command-line arguments
parser = argparse.ArgumentParser(description='Telnet into the device, save CDP neighbor information to a text file, and convert to a CSV file.')
parser.add_argument('-u', '--username', help='Telnet username', required=True)
parser.add_argument('-p', '--password', help='Telnet password', required=True)
parser.add_argument('-H', '--host', help='Telnet hostname or IP address', required=True)
parser.add_argument('-t', '--text_output', help='Output text file to store raw CDP neighbor information', required=True)
args = parser.parse_args()

# Telnet into the device, run 'show cdp neighbors detail', and save the output to the specified text file
telnet_and_save_cdp_neighbors(args.username, args.password, args.host, args.text_output)

# Read CDP neighbor information from the specified text file
with open(args.text_output, 'r') as file:
    cdp_neighbor_data = file.read()

parsed_neighbors = parse_cdp_neighbors(cdp_neighbor_data)

# Replace the .txt extension with .csv
csv_output = os.path.splitext(args.text_output)[0] + '.csv'

# Write the parsed information to the output CSV file
with open(csv_output, 'w', newline='') as csvfile:
    fieldnames = ['device_id', 'ip_address', 'platform', 'capabilities', 'interface']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for neighbor in parsed_neighbors:
        writer.writerow(neighbor)
