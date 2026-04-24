#!/usr/bin/env python3
import mysql.connector
import csv
import sys
import os
import datetime
import pwd
import socket

DB_CONFIG = {
    "host": "localhost",
    "user": "maki-quiz",
    "password": os.environ.get("QUIZ_DB_PASSWORD", "bfw01"),
    "database": "quiz_umschulung",
    "charset": "utf8mb4"
}

LOG_FILE = "/home/admin/import_log.txt" if os.name == "posix" else "import_log.txt"

def get_user_info():
    username = pwd.getpwuid(os.getuid()).pw_name
    ip = os.environ.get("SSH_CLIENT", "").split()[0] if "SSH_CLIENT" in os.environ else "lokal"
    return username, ip

def log_import(dateiname, anzahl, erste_id, letzte_id):
    username, ip = get_user_info()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"{timestamp} | Benutzer: {username} | IP: {ip} | "
                  f"Datei: {os.path.basename(dateiname)} | Fragen: {anzahl} | "
                  f"IDs: {erste_id} - {letzte_id}\n")

def importiere_csv(csv_datei):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    with open(csv_datei, 'r', encoding='utf-8') as f:
        first_line = f.readline()
        f.seek(0)
        delimiter = ',' if ',' in first_line else ';'
        reader = csv.reader(f, delimiter=delimiter)
        next(reader)  # Kopfzeile

        fragen_ids = []
        for row in reader:
            kat_ids_str = row[0].strip()
            if not kat_ids_str:
                print("⚠️ Zeile ohne Kategorie-IDs übersprungen.")
                continue
            try:
                kat_ids = [int(x.strip()) for x in kat_ids_str.split(',')]
            except ValueError:
                print(f"⚠️ Ungültige Kategorie-IDs: '{kat_ids_str}' – Zeile übersprungen.")
                continue

            fragetext = row[1].strip()
            erklaerung = row[2].strip()
            antworten = [row[3].strip(), row[4].strip(), row[5].strip(), row[6].strip()]
            korrekte_nr = int(row[7]) if row[7].strip() else None
            typ = row[8].strip().upper() if len(row) > 8 else ''

            if typ not in ('MC', 'FT'):
                print(f"⚠️ Ungültiger Typ '{typ}' – Frage übersprungen.")
                continue

            nicht_leer = [i for i, text in enumerate(antworten) if text != ""]

            cursor.execute(
                "INSERT INTO frage (fragetext, erklaerung, typ) VALUES (%s, %s, %s)",
                (fragetext, erklaerung, typ)
            )
            frage_id = cursor.lastrowid
            fragen_ids.append(frage_id)

            for kat_id in kat_ids:
                cursor.execute(
                    "INSERT INTO frage_kategorie (frage_id, kategorie_id) VALUES (%s, %s)",
                    (frage_id, kat_id)
                )

            if typ == 'FT':
                for idx in nicht_leer:
                    cursor.execute(
                        "INSERT INTO antwort (frage_id, antworttext, ist_korrekt) VALUES (%s, %s, 1)",
                        (frage_id, antworten[idx])
                    )
            else:  # MC
                if korrekte_nr is None or not (1 <= korrekte_nr <= 4):
                    print(f"⚠️ MC-Frage '{fragetext[:30]}...': korrekte_antwort_nr erforderlich – übersprungen.")
                    continue
                for i, antworttext in enumerate(antworten, start=1):
                    ist_korrekt = (i == korrekte_nr)
                    cursor.execute(
                        "INSERT INTO antwort (frage_id, antworttext, ist_korrekt) VALUES (%s, %s, %s)",
                        (frage_id, antworttext, ist_korrekt)
                    )

    conn.commit()
    anzahl = len(fragen_ids)
    if anzahl > 0:
        erste_id = fragen_ids[0]
        letzte_id = fragen_ids[-1]
        log_import(csv_datei, anzahl, erste_id, letzte_id)
        print(f"✅ Erfolgreich {anzahl} Fragen importiert (IDs {erste_id} - {letzte_id}).")
    else:
        print("⚠️ Keine Fragen importiert.")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Verwendung: python import_fragen.py <csv-datei>")
        sys.exit(1)
    importiere_csv(sys.argv[1])