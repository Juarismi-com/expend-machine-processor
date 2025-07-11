# report_ip.py
import requests
import socket

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
    url = "https://TU_BACKEND/api/update-ip"
    data = {"ip": ip, "key": "secreto123"}  # opcional: seguridad
    try:
        res = requests.post(url, json=data, timeout=5)
        print(f"[+] IP reportada: {ip} ({res.status_code})")
    except Exception as e:
        print(f"[!] Error al reportar IP: {e}")

if __name__ == "__main__":
    report_ip()