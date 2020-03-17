import os
import csv
import re
from bs4 import BeautifulSoup, NavigableString
from collections import defaultdict
from datetime import datetime
from functools import reduce

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
                return parse_time(txt)

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


top_dir = './wayback_dumps'
files = sorted(os.listdir(top_dir))

try:
    csv_path = "./csv"
    os.makedirs(csv_path)
except:
    pass

# 
# Status of cases
#
data = dict()
for f in files:
    path = os.path.join(top_dir, f)
    with open(path, 'r') as f:
        soup = BeautifulSoup(f, features='lxml')
        timestamp = last_update(soup)
        if timestamp:
            data[timestamp] = dict(status_of_cases(soup))

columns = sorted(reduce(lambda x,y: x|y.keys(), data.values(), set()))
with open(os.path.join(csv_path, "status_of_cases.csv"), "w") as f:
    writer = csv.writer(f)
    writer.writerow(["last_update"] + columns)
    for t, row in sorted(data.items()):
        writer.writerow([t] + [row.get(k) for k in columns])

#
# Individual cases
#

data = dict()
for f in files:
    path = os.path.join(top_dir, f)
    with open(path, 'r') as f:
        soup = BeautifulSoup(f, features='lxml')
        timestamp = last_update(soup)
        if timestamp:
            data[timestamp] = list(get_cases(soup))

columns = set()
for t, cases in data.items():
    for case in cases:
        columns = columns | case.keys()
columns = sorted(columns)

with open(os.path.join(csv_path, "cases.csv"), "w") as f:
    writer = csv.writer(f)
    writer.writerow(["last_update"] + columns)
    for t, cases in sorted(data.items()):
        for case in cases:
            writer.writerow([t] + [case.get(k) for k in columns])


