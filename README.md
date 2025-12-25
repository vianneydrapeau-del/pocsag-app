📦 Structure du projet
pocsag-app/
│
├── install.sh               # Script d'installation automatique
├── server.py                # Serveur FastAPI
├── pocsag_rtl.sh            # Script RTL-SDR + multimon-ng
├── requirements.txt         # Dépendances Python
│
├── systemd/
│   ├── pocsag-api.service   # Service API
│   └── pocsag-rtl.service   # Service RTL-SDR
│
├── static/
│   └── index.html           # Interface web
│
└── README.md

⚙️ Prérequis

Raspberry Pi (Raspberry Pi OS recommandé)

Clé RTL-SDR compatible

Connexion Internet

Accès root (sudo)

🧰 Installation rapide
1️⃣ Cloner le projet
git clone https://github.com/vianneydrapeau-del/pocsag-app.git
cd pocsag-app

2️⃣ Lancer l’installation
sudo ./install.sh


⏳ L’installation prend 1–2 minutes.

🌐 Accéder à l’interface web

Dans un navigateur :

http://IP_DU_RASPBERRY:8000


Exemple :

http://192.168.1.50:8000

🔄 Services installés
Service	Description
pocsag-api	Serveur web FastAPI
pocsag-rtl	Réception RTL-SDR
Vérifier l’état :
sudo systemctl status pocsag-api
sudo systemctl status pocsag-rtl

Redémarrer :
sudo systemctl restart pocsag-api
sudo systemctl restart pocsag-rtl

🧪 Dépannage
Voir les logs :
sudo journalctl -u pocsag-api -f
sudo journalctl -u pocsag-rtl -f

Tester l’API :
curl -X POST "http://127.0.0.1:8000/add?msg=TEST"

📡 Fréquence & configuration

La fréquence radio se règle dans :

pocsag_rtl.sh


Exemple :

rtl_fm -f 173.5125M ...

🧠 Notes

Les messages avec Function 0 sont ignorés automatiquement.

L’historique est conservé côté serveur.

Interface responsive (PC / mobile).
