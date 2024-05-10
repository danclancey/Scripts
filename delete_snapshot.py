"""
---------------------------------------------------------------
Script Name: OpenSearch Snapshot deletion management
Author: Dan Clancey
Date: 24-Oct-2023
Version: 1.0
Description:
    This script automates the management of OpenSearch repositories. 
    It periodically checks the number of repository snapshots and deletes the oldest one if the count exceeds 170. 
    It uses basic authentication for OpenSearch server requests. 
    The script also features an email notification system using Gmail's SMTP server for alerts in case of failures.

Usage:
    python delete_snapshot.py

Requirements:
    - Python 3.x
    - requests library: for making HTTP requests to the OpenSearch server.
    - smtplib library: for sending email notifications.
    - logging library: for logging actions and errors.
    - urllib3 library: for handling HTTP connections.

Notes:
    - Ensure that the OpenSearch server's URL, along with the username and password, are correctly configured in the script.
    - Update the email sender, recipient, and SMTP authentication details for the email notification functionality.
    - The script disables SSL warnings (InsecureRequestWarning) from urllib3, which may occur during connections to the OpenSearch server. 
      This is to prevent log clutter but consider the security implications in a production environment.
---------------------------------------------------------------
"""


import requests
import logging
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings
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
auth = (username, password)

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
        logging.info('Email sent!')
    except Exception as e:
        logging.error(f'Failed to send email: {e}')


def get_repositories():
    url = "https://opensearch01:9200/_cat/snapshots/my-fs-repository"
    response = requests.get(url, auth=auth, verify=False)
    if response.status_code != 200:
        logging.error(f"Failed to get repositories. Status code: {response.status_code}")
        return None
    repos = response.text.strip().split('\n')
    return [(repo.split()[0], repo) for repo in repos]

def delete_oldest_repository(oldest_repo_name):
    url = f"https://opensearch01:9200/_snapshot/my-fs-repository/{oldest_repo_name}"
    response = requests.delete(url, auth=auth, verify=False)
    if response.status_code != 200:
        logging.error(f"Failed to delete {oldest_repo_name}. Status code: {response.status_code}")
        send_email(
            'Repository Deletion Failed',
            f'Failed to delete {oldest_repo_name}. Status code: {response.status_code}',
            'recipient@email.com', # update with recipient email
            'sender@email.com', # update with sender email
            'senderpassword' # update with sender password
        )
    else:
        logging.info(f"Deleted oldest snapshot: {oldest_repo_name}")

def main():
    repos = get_repositories()
    if repos is None:
        return

    if len(repos) > 170:
        # Sorting repositories by name (which is date formatted)
        repos.sort(key=lambda x: x[0])
        oldest_repo_name, _ = repos[0]
        delete_oldest_repository(oldest_repo_name)
    else:
        logging.info("Snapshot count is below threshold. No action taken")

if __name__ == "__main__":
    main()
