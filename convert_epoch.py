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