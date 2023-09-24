"""
---------------------------------------------------------------
Script Name: OpenSearch Index Management and Snapshot Creator
Author: Dan
Date: 12-Jun-2023
Version: 1.0
Description:
    This script manages OpenSearch indices by querying the index status and creating snapshots. 
    It keeps the last 9 indices and creates snapshots for the rest before potentially removing them. 
    If the snapshot creation fails, it sends an email notification.

Usage:
    python opensearch_index_manager.py

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

import pytz
import re
import requests
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from urllib3.exceptions import InsecureRequestWarning


requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

username = 'opensearch_username'
password = 'opensearch_password'

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
    except Exception as e:
        print('Failed to send email:', e)

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
        print(f"Failed to create snapshot for {index_name}. Status code: {response.status_code}")
        send_email('Snapshot creation failed', f'Failed to create snapshot for {index_name}. Status code: {response.status_code}', 'recipient_email@gmail.com', 'sender_email@gmail.com', 'sender_password')
        return False
    return True

def get_indices():
    url = 'https://opensearch01:9200/_cat/indices?v=true&pretty'
    response = requests.get(url, auth=(username, password), verify=False)

    if response.status_code != 200:
        print(f"Request failed with status code {response.status_code}")
        return

    lines = response.text.split("\n")
    indices = []

    for line in lines:
        words = line.split()
        if words and words[0] == 'green':
            index = words[2]
            match = re.match(r"(.*?)_(\d+)", index)

            if match:
                base_name, rotation_number = match.groups()

                if base_name == 'firewall':
                    response = requests.get(f"https://opensearch01:9200/{index}/_settings", auth=(username, password), verify=False)
                    creation_date = response.json()[index]['settings']['index']['creation_date']
                    creation_date = datetime.fromtimestamp(int(creation_date) / 1000.0)
                    creation_date = pytz.utc.localize(creation_date).astimezone(pytz.timezone('US/Eastern'))
                    creation_date_formatted = creation_date.strftime("%Y-%m-%d_%I%M%p").lower()
                    indices.append((base_name, int(rotation_number), creation_date_formatted, index))
    indices.sort(key=lambda x: x[1])

    return indices

indices = get_indices()

indices_to_keep = indices[-9:]

for base_name, rotation_number, creation_date, index in indices:
    if (base_name, rotation_number, creation_date, index) not in indices_to_keep:
        if create_snapshot(index, creation_date, (username, password)):
            print(f"Created snapshot for {base_name}_{rotation_number}: {creation_date}")
