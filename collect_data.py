import csv
import paramiko
import time
from datetime import datetime
import locale
import os
import re
import pandas as pd

# --- FUNGSI UNTUK MEMBACA FILE ---
def read_hosts_from_csv(filename='hosts.csv'):
    """Membaca daftar host dari file CSV."""
    hosts = []
    try:
        with open(filename, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                hosts.append(row)
    except FileNotFoundError:
        print(f"Error: File '{filename}' tidak ditemukan.")
    return hosts

def read_commands_from_txt(filename='commands.txt'):
    """Membaca daftar perintah dari file TXT."""
    commands = []
    try:
        with open(filename, 'r') as f:
            commands = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print(f"Error: File '{filename}' tidak ditemukan.")
    return commands

# --- FUNGSI UNTUK MENGOLAH OUTPUT PERINTAH ---
def parse_df_output(output):
    """Mengolah output df -lh untuk mendapatkan detail penggunaan disk partisi root."""
    data = {}
    lines = output.strip().split('\n')
    # Temukan baris yang terpasang pada root '/'
    root_line = None
    for line in lines:
        if line.strip().endswith(' /'):
            root_line = line
            break

    if root_line:
        parts = root_line.split()
        if len(parts) >= 6:
            # Perbarui: Menggunakan indeks untuk memastikan urutan yang benar
            data['/dev/mapper/ Total'] = parts[1]
            data['/dev/mapper/ Used'] = parts[2]
            data['/dev/mapper/ Available'] = parts[3]
            data['/dev/mapper/ %Used'] = parts[4]
    
    return data

def parse_meminfo_output(output):
    """Mengolah output cat /proc/meminfo untuk mendapatkan penggunaan memori."""
    data = {}
    lines = output.strip().split('\n')
    
    mem_total_kb = 0
    mem_available_kb = 0
    for line in lines:
        if 'MemTotal:' in line:
            mem_total_kb = int(re.search(r'(\d+)', line).group(1))
            data['MemTotal'] = f"{mem_total_kb} kB"
        if 'MemFree:' in line:
            data['MemFree'] = re.search(r'(\d+)', line).group(1) + ' kB'
        if 'MemAvailable:' in line:
            mem_available_kb = int(re.search(r'(\d+)', line).group(1))
            data['MemAvailable'] = f"{mem_available_kb} kB"
    
    if mem_total_kb > 0:
        percent_available = (mem_available_kb / mem_total_kb) * 100
        data['%MemAvailable'] = f"{percent_available:.2f}%"

    return data

def parse_lscpu_output(output):
    """Mengolah output lscpu untuk mendapatkan detail CPU."""
    data = {}
    data['Architecture'] = re.search(r'Architecture:\s*(.*)', output).group(1).strip()
    data['CPU(s)'] = re.search(r'CPU\(s\):\s*(.*)', output).group(1).strip()
    data['Vendor ID'] = re.search(r'Vendor ID:\s*(.*)', output).group(1).strip()
    data['Model name'] = re.search(r'Model name:\s*(.*)', output).group(1).strip()
    return data

def parse_uptime_output(output):
    """Mengolah output uptime untuk mendapatkan load average."""
    data = {}
    match = re.search(r'load average:\s*(\d+\.\d+),\s*(\d+\.\d+),\s*(\d+\.\d+)', output)
    if match:
        data['%CPU 1mins'] = float(match.group(1))
        data['%CPU 5mins'] = float(match.group(2))
        data['%CPU 15mins'] = float(match.group(3))
    return data

# --- PETA PEMETAAN (COMMANDS TO PARSING FUNCTIONS) ---
command_parsers = {
    "cat /etc/redhat-release": lambda output: {'Operating System': output.strip()},
    "lscpu": parse_lscpu_output,
    "cat /proc/meminfo": parse_meminfo_output,
    "df -lh": parse_df_output,
    "uptime": parse_uptime_output
}

# --- FUNGSI UTAMA ---
def run_command_on_host(hostname, ip, user, passwd, command_list):
    print(f"--- Connecting to {hostname} ({ip}) ---")
    host_data_for_excel = {'hostname': hostname}
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=user, password=passwd, timeout=10)
        
        try:
            locale.setlocale(locale.LC_TIME, 'id_ID.UTF-8')
        except locale.Error:
            pass

        current_time_str = datetime.now().strftime("%A_%d-%B-%Y-%H%M%S")
        log_filename = f"{hostname}_healtcheck_{current_time_str}.log"
        log_folder = "log"
        os.makedirs(log_folder, exist_ok=True)
        full_log_path = os.path.join(log_folder, log_filename)

        with open(full_log_path, 'w') as log_file:
            log_file.write(f"--- Data collected from {hostname} ({ip}) ---\n\n")
            
            for cmd in command_list:
                log_file.write(f"========================================\n")
                log_file.write(f"Executing: {cmd}\n")
                log_file.write(f"========================================\n\n")

                stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
                
                output = stdout.read().decode('utf-8')
                error = stderr.read().decode('utf-8')
                
                log_file.write(output)
                if error:
                    log_file.write(f"\n--- ERROR ---\n{error}\n")
                log_file.write("\n\n")
                
                if cmd in command_parsers:
                    parsed_data = command_parsers[cmd](output)
                    host_data_for_excel.update(parsed_data)
        
        print(f"--- Data from {hostname} saved to {full_log_path} ---")
    except paramiko.AuthenticationException:
        print(f"Error: Authentication failed for {hostname}.")
    except paramiko.SSHException as e:
        print(f"Error: SSH connection failed for {hostname}. Reason: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        ssh.close()
        print(f"--- Disconnected from {hostname} ---")
        print("-" * 50)
        return host_data_for_excel

def process_and_export_to_excel(all_hosts_data):
    """Menulis data yang dikumpulkan ke file Excel."""
    try:
        df = pd.DataFrame(all_hosts_data)
        
        excel_filename = f"inventory_report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
        df.to_excel(excel_filename, index=False)
        print(f"Laporan berhasil disimpan ke {excel_filename}")
    except Exception as e:
        print(f"Gagal membuat laporan Excel: {e}")

if __name__ == "__main__":
    
    host_list = read_hosts_from_csv()
    commands = read_commands_from_txt()
    
    all_hosts_data = []
    
    if host_list and commands:
        for host in host_list:
            data = run_command_on_host(
                host['hostname'],
                host['ip_address'],
                host['username'],
                host['password'],
                commands
            )
            if data:
                all_hosts_data.append(data)
    
    if all_hosts_data:
        process_and_export_to_excel(all_hosts_data)
    else:
        print("Tidak ada data yang dikumpulkan. File Excel tidak akan dibuat.")