# Healthcheck_Redhat_Rizkyprsis
Script ini dibuat oleh rizkyprsis
Script ini memudahkan untuk collect data Healthcheck Linux dan otomatis 
mengolahnya menjadi file Excel dan file .txt
Mudah untuk digunakan, hanya perlu memodifikasi list commands dan juga list hosts.csv nya

<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/d36d3b8d-162a-4f32-97a5-d09b42ccec31" />

requirement :

redhat can accessed ssh using local credential

[vagrant@JKT-Redhat-04 ~]$ sudo cat /etc/ssh/sshd_config | grep Password
PasswordAuthentication yes (uncomment)
#PermitEmptyPasswords no
PasswordAuthentication no

add user as sudoers

example : 
[automation@SBY-Redhat-03 ~]$ echo "automation ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/auto
mation

[automation@SBY-Redhat-03 ~]$ sudo cat /etc/sudoers.d/automation
automation ALL=(ALL) NOPASSWD: ALL

Script ini bebas digunakan untuk siapapun
inventory_report adalah file excel yang ter-generate otomatis
file .txt didalam folder log adalah file collect data cli pada linux
