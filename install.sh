#!/bin/bash

set -e

echo "=== Installation POCSAG ==="

# Vérification root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Lance ce script avec sudo"
  exit 1
fi

USER_NAME=$(logname)
HOME_DIR="/home/$USER_NAME"
APP_DIR="$HOME_DIR/pocsag-app"

echo "Utilisateur : $USER_NAME"
echo "Dossier : $APP_DIR"

# Mise à jour
apt update

# Dépendances système
apt install -y \
  git \
  python3 \
  python3-venv \
  python3-pip \
  rtl-sdr \
  sox \
  multimon-ng

# Permissions RTL-SDR
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="0bda", ATTRS{idProduct}=="2838", MODE="0666"' > /etc/udev/rules.d/20-rtl-sdr.rules
udevadm control --reload-rules
udevadm trigger

# Python venv
cd "$APP_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn

# Copier les services systemd
cp systemd/*.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reexec
systemctl daemon-reload

# Activer services
systemctl enable pocsag-api.service
systemctl enable pocsag-rtl.service

# Démarrer
systemctl start pocsag-api.service
systemctl start pocsag-rtl.service

echo "✅ Installation terminée"
echo "Interface web: http://$(hostname -I | awk '{print $1}'):8000"
