import csv

try:
    with open('hosts.csv', mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        # Mencetak nama kolom (headers) yang ditemukan
        print("Headers found:", reader.fieldnames)
        
except FileNotFoundError:
    print("Error: 'hosts.csv' not found. Make sure the file exists.")