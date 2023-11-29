"""
---------------------------------------------------------------
Script Name: OpenSearch Index Management and Snapshot Creator
Author: Dan Clancey
Date: 12-Jun-2023
Version: 1.0
Description:
    This script manages OpenSearch indices by querying the index status and creating snapshots. 
    It keeps the last 9 indices and creates snapshots for the rest before potentially removing them. 
    If the snapshot creation fails, it sends an email notification.

Usage:
    python create_snapshot.py

Requirements:
    - Python 3.x
    - pytz library
    - requests library
    - smtplib library
    - re library

Notes:
    - You must have authentication credentials for both OpenSearch and the Gmail SMTP server.
    - This script uses the urllib3 library, which will raise InsecureRequestWarnings if the verification of SSL certificates is disabled.
    To suppress these warnings, the script has disabled these specific warnings.
---------------------------------------------------------------
"""

import logging
import pytz
import re
import requests
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from requests.packages.urllib3.exceptions import InsecureRequestWarning


requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# Set up logging
logging.basicConfig(
    filename='/var/log/graylog-server/repository_management.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

username = 'admin' # update with OS username
password = 'password' # update with OS password

def send_email(subject, body, to, gmail_user, gmail_pwd):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = gmail_user
    msg['To'] = to

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_pwd)
        server.send_message(msg)
        server.close()
        print('Email sent!')
        logging.info('Email sent!')
    except Exception as e:
        logging.error(f'Failed to send email: {e}')

def create_snapshot(index_name, snapshot_name, auth, verify=False):
    """Creates a snapshot for the given index"""
    url = f"https://opensearch01:9200/_snapshot/my-fs-repository/{snapshot_name}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "indices": index_name,
        "ignore_unavailable": True,
        "include_global_state": False
    }
    response = requests.put(url, auth=auth, headers=headers, json=payload, verify=False)
    print(response.text)
    if response.status_code != 200:
        logging.error(f"Failed to create snapshot for {index_name}. Status code: {response.status_code}")
        send_email('Snapshot creation failed', f'Failed to create snapshot for {index_name}. Status code: {response.status_code}', 'recipient@email.com', 'sender@email.com', 'sender password') # update recipient email, sender email/password
        return False
    return True

def get_indices():
    # URL of your Elasticsearch instance
    url = 'https://opensearch01:9200/_cat/indices?v=true&pretty'

    # Make the GET request to Elasticsearch
    response = requests.get(url, auth=(username, password), verify=False)
    # Check that the request was successful
    if response.status_code != 200:
        logging.error(f"Request failed with status code {response.status_code}")
        return

    # Split the response into lines
    lines = response.text.split("\n")

    # Initialize an empty dictionary to store the indices and their creation date
    indices = []

    # Loop over each line
    for line in lines:
        # Split the line into words
        words = line.split()

        # If the line has words and the first word is "green", it's an index
        if words and words[0] == 'green':
            # The index name is the third word
            index = words[2]

            # Extract the base name and the rotation number using a regex
            match = re.match(r"(.*?)_(\d+)", index)

            # If the index name matches the pattern
            if match:
                base_name, rotation_number = match.groups()

                if base_name == 'firewall':
                    # Get the creation date of the index
                    response = requests.get(f"https://opensearch01:9200/{index}/_settings", auth=(username, password), verify=False)
                    creation_date = response.json()[index]['settings']['index']['creation_date']

                    # Convert the creation date to a datetime object
                    creation_date = datetime.fromtimestamp(int(creation_date) / 1000.0)

                    # Convert the datetime object to the desired timezone
                    creation_date = pytz.utc.localize(creation_date).astimezone(pytz.timezone('US/Eastern'))

                    # Format the datetime object as a string
                    creation_date_formatted = creation_date.strftime("%Y-%m-%d_%I%M%p").lower()

                    # Add the index to the list as a tuple of base name, rotation number (as an integer), and full index name
                    indices.append((base_name, int(rotation_number), creation_date_formatted, index))

    # Sort the list of indices
    # This will sort by base name first, then rotation number
    indices.sort(key=lambda x: x[1])

    # Return the sorted list of indices
    return indices

indices = get_indices()

# Keep the most recent 9 indices
indices_to_keep = indices[-9:]

# Create a snapshot for the older indices
for base_name, rotation_number, creation_date, index in indices:
    if (base_name, rotation_number, creation_date, index) not in indices_to_keep:
        if create_snapshot(index, creation_date, (username, password)):
            logging.info(f"Created snapshot for {base_name}_{rotation_number}: {creation_date}")
rotation_number}: {creation_date}")
