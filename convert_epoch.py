"""
---------------------------------------------------------------
Script Name: Epoch Time Converter
Author: Dan Clancey
Date: 7-May-2023
Version: 1.0
Description:
    This script converts a given epoch time to a human-readable datetime string formatted as "YYYY-MM-DD_HHMM",
    adjusting for the US Eastern timezone.

Usage:
    python convert_epoch.py [epoch_time]

    Where:
    [epoch_time] is the epoch time to convert, specified as an integer.

Examples:
    python epoch_time_converter.py 1619710738000
    Output: 2023-04-29_0806PM

Requirements:
    - Python 3.x
    - argparse library
    - datetime library
    - pytz library
---------------------------------------------------------------
"""

import argparse
import datetime
import pytz

# Create the parser and add args
parser = argparse.ArgumentParser(description='Convert epoch time to datetime')
parser.add_argument('EpochTime', metavar='epoch_time', type=int,
                    help='the epoch time to convert')

args = parser.parse_args()

# Convert and format time from Epoch to YYY-MM-DD_HHMM
creation_date = datetime.datetime.fromtimestamp(args.EpochTime / 1000.0)
creation_date = pytz.utc.localize(creation_date)
creation_date = creation_date.astimezone(pytz.timezone('US/Eastern'))
creation_date_formatted = creation_date.strftime("%Y-%m-%d_%I%M%p")

print(creation_date_formatted)
