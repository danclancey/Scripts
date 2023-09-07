"""
.SYNOPSIS
    Fetches configurations of Cisco switches via SSH (and Telnet as a fallback) and saves them locally.

.DESCRIPTION
    This script reads a list of Cisco switch IP addresses from a specified file. For each IP, it attempts to connect using SSH
    (with provided credentials) to fetch the running configuration. If the SSH connection fails, it attempts a Telnet connection.
    Retrieved configurations are saved to individual files, named based on the switch IP and the current timestamp, in the
    ~/configs/switches/<SwitchIP>/ directory.

.NOTES
    File Name      : BulkFetch-SwitchConfig.py
    Author         : Dan Clancey
    Prerequisite   : Python 3.x, paramiko, pytz, telnetlib
    Date           : 29-Jun-2023
    Version        : 1.0

.EXAMPLE
    python3 Fetch-SwitchConfig.py -file ~/config/switches/allswitches.txt -username admin -password secret

    This will attempt to fetch configurations for all switches listed in the allswitches.txt file using the provided credentials and save them in the respective directories.
"""


import paramiko
import argparse
import os
import paramiko
import telnetlib
from datetime import datetime
from pytz import timezone
import pytz

def ssh_and_save_config(ip, username, password):
    """SSH into the switch and save the config."""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password)

        # Assuming the switch is a Cisco device running IOS
        stdin, stdout, stderr = ssh.exec_command('show run')
        config_data = stdout.read().decode('utf-8')
        ssh.close()

    except paramiko.ssh_exception.AuthenticationException:
        raise

    except Exception as e:
        # If SSH fails, try Telnet
        print(f"SSH failed for {ip}. Trying Telnet...")
        try:
            tn = telnetlib.Telnet(ip)
            tn.read_until(b"Username: ")
            tn.write(username.encode('ascii') + b"\n")
            tn.read_until(b"Password: ")
            tn.write(password.encode('ascii') + b"\n")

            # Depending on your device, the next prompts might differ. Adjust as needed.
            tn.write(b"terminal length 0\n")  # Set terminal length to 0 for no pagination
            tn.write(b"show run\n")
            tn.write(b"exit\n")
            config_data = tn.read_all().decode('utf-8')
        except Exception as te:
            raise Exception(f"Telnet also failed for {ip} with error: {te}")

    # Check and create the directory for specific Switch IP if it doesn't exist
    directory = os.path.expanduser(f'~/configs/switches/{ip}')
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Save to file
    eastern = timezone('US/Eastern')
    current_time = datetime.now(eastern).strftime('%Y%m%d-%I%M%p')
    filepath = os.path.join(directory, f"{ip}-{current_time}.txt")
    with open(filepath, 'w') as file:
        file.write(config_data)

def main():
    parser = argparse.ArgumentParser(description="Fetch Cisco Switch Configurations")
    parser.add_argument("-file", type=str, required=True, help="File containing switch IP addresses")
    parser.add_argument("-username", type=str, required=True, help="SSH username")
    parser.add_argument("-password", type=str, required=True, help="SSH password")
    
    args = parser.parse_args()
    
    # Ensure the config directory exists
    directory = os.path.expanduser('~/configs/switches')
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Read IPs and fetch config
    with open(args.file, 'r') as f:
        for line in f:
            ip = line.strip()
            if ip:
                try:
                    ssh_and_save_config(ip, args.username, args.password)
                    print(f"Saved config for {ip}")
                except Exception as e:
                    print(f"Error fetching config for {ip}: {e}")


if __name__ == "__main__":
    main()

