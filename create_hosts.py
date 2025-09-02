import csv

hosts_data = [
    ['hostname', 'ip_address', 'username', 'password'],
    ['rhel-01', '192.168.1.10', 'rizky', 'rizky123'],
    ['rhel-02', '192.168.1.11', 'sisindo', 'sisindo123']
]

with open('hosts.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerows(hosts_data)

print("File hosts.csv berhasil dibuat.")