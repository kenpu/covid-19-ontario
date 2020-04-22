import requests
import subprocess
import time
import os
import csv
import re
from bs4 import BeautifulSoup, NavigableString
from collections import defaultdict
from datetime import datetime
from functools import reduce
from pprint import pprint

url = "https://www.ontario.ca/page/2019-novel-coronavirus"
status_of_cases_csv = "./csv/status_of_cases.csv"
status_of_cases_csv_v2 = './csv/status_of_cases_v2.csv'
cases_csv = "./csv/cases.csv"

def save_status(t, status):
    t = str(t)
    print("> %s" % status_of_cases_csv_v2)
    pprint(status)
    if os.path.exists(status_of_cases_csv_v2):
        with open(status_of_cases_csv_v2, 'r') as f:
            rdr = csv.reader(f)
            rows = list(rdr)
    else:
        rows = []

    with open(status_of_cases_csv_v2, 'a+') as f:
        writer = csv.writer(f)
        if len(rows) == 0:
            print("Creating...")
            columns = ['last_update'] + sorted(status.keys())
            row = [t] + [status.get(k) for k in columns[1:]]
            writer.writerow(columns)
            writer.writerow(row)
        else:
            columns = rows[0]
            ts = set([x[0] for x in rows[1:]])
            if t in ts:
                print("Skipping...")
            else:
                print("Saving...")
                row = [t] + [status.get(k) for k in columns[1:]]
                writer.writerow(row)

def get_snapshot():
    cmd = ['google-chrome',
            '--headless', 
            '--disable-gpu', 
            '--run-all-compositor-stages-before-draw', 
            '--dump-dom', 
            '--virtual-time-budget=10000',
            url]
    p = subprocess.run(cmd, stdout=subprocess.PIPE)
    soup = BeautifulSoup(p.stdout, features='lxml')
    return soup

def is_status_of_cases_table(elem_table):
    text = elem_table.get_text().lower()
    return "summary of cases" in text

def get_status_of_cases_table(soup):
    for elem in soup.find_all('table'):
        if is_status_of_cases_table(elem):
            return elem

def status_of_cases_entry(td1, td2):
    key = td1.get_text().lower()
    val = td2.get_text()

    if 'number of cases' in key:
        k = "number_of_cases"
    elif 'resolved' in key:
        k = 'resolved'
    elif 'deceased' in key:
        k = 'deceased'
    elif 'male' in key:
        k = 'male'
    elif 'female' in key:
        k = 'female'
    elif '19 and under' in key:
        k = 'under_19'
    elif '20-64' in key:
        k = 'between_20_64'
    elif '65 and over' in key:
        k = 'over_65'
    elif 'total tests completed' in key and not ("previous day" in key):
        k = 'total_tested'
    elif 'currently under investigation' in key:
        k = 'investigation'
    else:
        k = None

    v = td2.get_text()
    v = int(v.replace(',', ''))
    return k,v

def status_of_cases(table):
    elems = []
    for tr in table.find_all('tr'):
        td_list = tr.find_all('td')
        if len(td_list) == 3:
            try:
                k, v = status_of_cases_entry(td_list[0], td_list[1])
                if k and v:
                    elems.append((k,v))
            except:
                pass
    return dict(elems)

def parse_time(txt):
    return datetime.strptime(txt, "%B %d, %Y")

def last_update(soup):
    for small in soup.find_all('small'):
        text = small.get_text()
        m = re.search(r'Updated: (\S+\s+\d+,\s+\d+)', text)
        if m:
            return parse_time(m.group(1))

if __name__ == '__main__':
    soup = get_snapshot()
    table = get_status_of_cases_table(soup)
    if table:
        status = status_of_cases(table)
        t = last_update(soup)
        print("== %s ==" % t)
        if t:
            save_status(t, status)
        else:
            print("Cannot figure out timestamp.")
    else:
        print("Cannot find status table")
