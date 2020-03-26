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
cases_csv = "./csv/cases.csv"

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
    return 'negative' in text \
            and 'confirmed' in text \
            and 'positive' in text \
            and 'resolved' in text \
            and 'total number' in text

def get_status_of_cases_table(soup):
    for elem in soup.find_all('table'):
        if is_status_of_cases_table(elem):
            return elem

def status_of_cases_entry(td1, td2):
    text = td1.get_text().lower()
    if 'confirmed negative' in text:
        k = 'negative'
    elif 'presumptive negative' in text:
        k = None
    elif 'negative' in text:
        k = 'negative'
    elif 'presumptive positive' in text:
        k = 'positive_presumptive'
    elif 'confirmed positive' in text:
        k = 'positive_confirmed'
    elif 'positive' in text:
        k = 'positive'
    elif 'resolved' in text:
        k = 'resolved'
    elif 'approved for covid' in text \
            and 'testing' in text:
        k = 'approved_testing'
    v = int(td2.get_text())
    return k,v

def status_of_cases(table):
    for tr in table.find_all('tr'):
        td_list = tr.find_all('td')
        if len(td_list) == 2:
            try:
                k, v = status_of_cases_entry(td_list[0], td_list[1])
                if k and v:
                    yield k, v
            except:
                pass

def parse_time(txt):
    txt = txt.strip().split(":", 1)[1]
    date, tm = txt.split(" at ", 1)
    date = date.strip().capitalize()
    tm = tm.strip().replace(".", "")
    return datetime.strptime("%s %s" % (date, tm), "%B %d, %Y %I:%M %p")

def last_update(soup):
    for elem in soup.find_all(name='abbr', attrs=dict(title="Eastern Time")):
        txt = elem.parent.contents[0]
        if isinstance(txt, NavigableString):
            txt = txt.lower()
            if txt.startswith("last updated:"):
                return str(parse_time(txt))

def get_case_table(soup):
    for elem in soup.find_all('thead'):
        txt = elem.get_text().lower()
        if 'case number' in txt and 'public health unit' in txt:
            return elem.parent

def column_name(txt):
    txt = re.sub(r'\(.*\)', '', txt).strip().lower()
    txt = re.sub(r'\s+', '_', txt)
    return txt

def clean_text(txt):
    txt = txt.strip()
    return txt

def get_cases(soup):
    table = get_case_table(soup)
    if table:
        th = table.thead.find_all('th')
        columns = [column_name(x.get_text().lower()) for x in th]

        for tr in table.tbody.find_all('tr'):
            row = [x.get_text().lower() for x in tr.find_all('td')]
            row[0] = int(row[0])
            row[1:] = [clean_text(x) for x in row[1:]]
            yield dict(zip(columns, row))
            
def save_status(t, status):
    with open(status_of_cases_csv, 'r') as f:
        rdr = csv.reader(f)
        columns = next(rdr)
        data = set(x[0] for x in rdr)
    row = [t] + [status.get(c) for c in columns[1:]]
    if t in data:
        print("Skipping status: %s" % t)
    else:
        with open(status_of_cases_csv, 'a+') as f:
            writer = csv.writer(f)
            writer.writerow(row)
            print("Saved: @%s %s" % (t, str(status)))
            
def save_cases(t, cases):
    with open(cases_csv, 'r') as f:
        rdr = csv.reader(f)
        columns = next(rdr)
        data = set(x[0] for x in rdr)
    for case in cases:
        row = [t] + [case.get(x) for x in columns[1:]]
        if t in data:
            print("Skipping case:", row)
        else:
            print("Saving:", row)
            with open(cases_csv, 'a+') as f:
                writer = csv.writer(f)
                writer.writerow(row)
                
            
if __name__ == '__main__':
    soup = get_snapshot()
    t = last_update(soup)
    if t:
        # Status
        status = dict(status_of_cases(soup))
        save_status(t, status)
        # Cases
        cases = list(get_cases(soup))
        save_cases(t, cases)
