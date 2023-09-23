import pandas as pd
import requests
from bs4 import BeautifulSoup

file = input('Enter File Name: ')
file_out = input('Enter Output File Name of URL list: ')

with open(file) as f:
    for line in f:
        URL = "https://www.fortiguard.com/webfilter"
        address = str(line)
        headers = {"Cookie":"cookiesession1=YOURCOOKIE"}
        PARAMS = {'q':address.rstrip(), 'version':'9'}

        r = requests.get(url = URL, headers=headers, params = PARAMS)
        data = r.text
        soup = BeautifulSoup(data, features="html.parser")
        category = soup.find("meta", attrs={'property': 'description' })

        file = open(file_out, "a")
        
        new_line = str(address).rstrip() + '\t' + category["content"]
        #print(new_line)
        file.write(new_line + '\n')

        file.close()

df = pd.read_csv(file_out, sep='\t', header=None)

print(df)