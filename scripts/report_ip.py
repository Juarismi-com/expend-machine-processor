# report_ip.py
import requests
import socket
import sys, os

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # conexión ficticia para determinar la IP
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def report_ip():
    ip = get_local_ip()
    url = "https://squid-app-bbs42.ondigitalocean.app/maquinas-ips/19bebe9a-faf1-45e9-9efc-094de55b0d6d" 
    data = {"ip": ip}  # opcional: seguridad
    try:
        res = requests.post(url, json=data, timeout=5)
        print(f"[+] IP reportada: {ip} ({res.status_code})")
    except Exception as e:
        print(f"[!] Error al reportar IP: {e}")

if __name__ == "__main__":
    report_ip()