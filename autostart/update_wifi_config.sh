#!/bin/bash

CONFIG_FILE="/etc/NetworkManager/system-connections/preconfigured.nmconnection"
SSID="$1"
PSK="$2"

# Validar entradas simples
if [ -z "$SSID" ] || [ -z "$PSK" ]; then
  echo "SSID or PSK missing"
  exit 1
fi

# Reemplazar ssid y psk
sed -i "s/^ssid=.*/ssid=${SSID}/" "$CONFIG_FILE"
sed -i "s/^psk=.*/psk=${PSK}/" "$CONFIG_FILE"

# Asignar permisos y reiniciar servicio
chmod 600 "$CONFIG_FILE"
systemctl restart NetworkManager
