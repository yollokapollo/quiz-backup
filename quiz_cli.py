#!/usr/bin/env python3
import mysql.connector
import random
import sys
import bcrypt
import os
import logging
import platform
import tempfile

# ------------------------------------------------------------------
# Session für eingeloggten Benutzer (einmal pro Programmstart)
# ------------------------------------------------------------------
current_user_id = None
current_user_name = None
current_user_kuerzel = None

# ------------------------------------------------------------------
# LOGGING KONFIGURIEREN (plattformunabhängig)
# ------------------------------------------------------------------
if platform.system() == "Linux":
    LOG_FILE = "/home/quiz/quiz.log"
else:
    LOG_FILE = os.path.join(tempfile.gettempdir(), "quiz.log")

log_dir = os.path.dirname(LOG_FILE)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_event(event, username="SYSTEM", details=""):
    message = f"User: {username} | {event}"
    if details:
        message += f" | Details: {details}"
    logging.info(message)

# ------------------------------------------------------------------
# DATENBANK-KONFIGURATION
# ------------------------------------------------------------------
_db_password = None

def get_db_config():
    global _db_password
    if _db_password is None:
        _db_password = os.environ.get("QUIZ_DB_PASSWORD")
        if _db_password is None:
            _db_password = input("Datenbank-Passwort für 'maki-quiz': ")
    return {
        "host": "localhost",
        "user": "maki-quiz",
        "password": _db_password,
        "database": "quiz_umschulung",
        "charset": "utf8mb4",
        "collation": "utf8mb4_general_ci"
    }

def connect_db():
    try:
        config = get_db_config()
        return mysql.connector.connect(**config)
    except mysql.connector.Error as err:
        log_event("Datenbankverbindung fehlgeschlagen", details=str(err))
        print("❌ Keine Verbindung zur Datenbank möglich. Bitte Administrator kontaktieren.")
        sys.exit(1)

def ensure_login(conn, cursor):
    global current_user_id, current_user_name, current_user_kuerzel
    if current_user_id is not None:
        return current_user_id, current_user_name, current_user_kuerzel
    user_id, name, kuerzel = benutzer_login(cursor, conn)
    current_user_id = user_id
    current_user_name = name
    current_user_kuerzel = kuerzel
    return user_id, name, kuerzel

# ------------------------------------------------------------------
# AUTHENTIFIZIERUNG
# ------------------------------------------------------------------
def benutzer_login(cursor, conn):
    while True:
        kuerzel = input("Benutzerkürzel: ").strip()
        cursor.execute(
            "SELECT benutzer_id, name, passwort_hash FROM benutzer WHERE kuerzel = %s",
            (kuerzel,)
        )
        user = cursor.fetchone()
        if user:
            benutzer_id, name, pw_hash = user
            if pw_hash is None:
                print("Für diesen Benutzer ist noch kein Passwort gesetzt.")
                neues_pw = input("Bitte neues Passwort vergeben: ").strip()
                if not neues_pw:
                    print("Passwort darf nicht leer sein.")
                    continue
                hashed = bcrypt.hashpw(neues_pw.encode('utf-8'), bcrypt.gensalt())
                cursor.execute(
                    "UPDATE benutzer SET passwort_hash = %s WHERE benutzer_id = %s",
                    (hashed.decode('utf-8'), benutzer_id)
                )
                conn.commit()
                print(f"Passwort für {name} wurde gespeichert.")
                log_event("Passwort gesetzt", username=kuerzel)
                return benutzer_id, name, kuerzel
            else:
                eingabe = input("Passwort: ").strip()
                if bcrypt.checkpw(eingabe.encode('utf-8'), pw_hash.encode('utf-8')):
                    print(f"Willkommen zurück, {name}!")
                    log_event("Login erfolgreich", username=kuerzel)
                    return benutzer_id, name, kuerzel
                else:
                    print("Falsches Passwort.")
                    log_event("Fehlgeschlagener Login-Versuch", username=kuerzel)
                    continue
        else:
            print("Neuer Benutzer – bitte registrieren.")
            name = input("Voller Name: ").strip()
            passwort = input("Passwort: ").strip()
            if not name or not passwort:
                print("Name und Passwort sind erforderlich.")
                continue
            hashed = bcrypt.hashpw(passwort.encode('utf-8'), bcrypt.gensalt())
            cursor.execute(
                "INSERT INTO benutzer (kuerzel, name, passwort_hash) VALUES (%s, %s, %s)",
                (kuerzel, name, hashed.decode('utf-8'))
            )
            conn.commit()
            benutzer_id = cursor.lastrowid
            print(f"Benutzer {name} wurde angelegt. Viel Erfolg!")
            log_event("Neuer Benutzer registriert", username=kuerzel, details=f"Name: {name}")
            return benutzer_id, name, kuerzel

def authentifiziere_benutzer():
    conn = connect_db()
    cursor = conn.cursor()
    kuerzel = input("Benutzerkürzel: ").strip()
    cursor.execute(
        "SELECT benutzer_id, name, passwort_hash FROM benutzer WHERE kuerzel = %s",
        (kuerzel,)
    )
    user = cursor.fetchone()
    if not user:
        print("Benutzer nicht gefunden.")
        cursor.close()
        conn.close()
        return None
    benutzer_id, name, pw_hash = user
    if pw_hash is None:
        print("Kein Passwort gesetzt. Bitte zuerst im Quiz anmelden.")
        cursor.close()
        conn.close()
        return None
    passwort = input("Passwort: ").strip()
    if bcrypt.checkpw(passwort.encode('utf-8'), pw_hash.encode('utf-8')):
        cursor.close()
        conn.close()
        return benutzer_id, name
    else:
        print("Falsches Passwort.")
        cursor.close()
        conn.close()
        return None

# ------------------------------------------------------------------
# KATEGORIE-HILFSFUNKTIONEN
# ------------------------------------------------------------------
def gesamtanzahl_fragen():
    """Gibt die Gesamtzahl aller Fragen zurück (ohne Kategorie 1)."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(DISTINCT frage_id) FROM frage_mit_kategorie WHERE kategorie_id != 1")
    anz = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return anz

# ------------------------------------------------------------------
# KATEGORIEN-MENÜ (HIERARCHISCH)
# ------------------------------------------------------------------
def waehle_kategorie_bereich():
    while True:
        print("\n--- KATEGORIEBEREICH WÄHLEN ---")
        print("1. Gemischt (alle Fragen)")
        print("2. BFW-Module (Unterrichtsinhalte)")
        print("3. Prüfungsvorbereitung (AP I / AP II)")
        wahl = input("Auswahl: ").strip()
        if wahl == "1":
            return [1]
        elif wahl == "2":
            return waehle_unterkategorien(2, 9, "BFW-Module")
        elif wahl == "3":
            return waehle_unterkategorien(10, 15, "Prüfungsvorbereitung")
        else:
            print("Ungültige Eingabe. Bitte 1, 2 oder 3 wählen.")

def waehle_unterkategorien(von_id, bis_id, titel):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT k.kategorie_id, k.bezeichnung, COUNT(DISTINCT fk.frage_id) AS anzahl
        FROM kategorie k
        LEFT JOIN frage_kategorie fk ON k.kategorie_id = fk.kategorie_id
        WHERE k.kategorie_id BETWEEN %s AND %s
        GROUP BY k.kategorie_id
        ORDER BY k.kategorie_id
    """, (von_id, bis_id))
    kategorien = cursor.fetchall()
    cursor.close()
    conn.close()

    if not kategorien:
        print(f"Keine Kategorien im Bereich '{titel}' vorhanden.")
        return []

    print(f"\n--- {titel.upper()} ---")
    for kat in kategorien:
        print(f"{kat[0]}: {kat[1]} ({kat[2]} Fragen)")

    print("\nMehrfachauswahl möglich (z.B. '2,4,7' oder 'alle' für alle in diesem Bereich).")
    eingabe = input("Deine Wahl: ").strip().lower()

    if eingabe == 'alle':
        return [kat[0] for kat in kategorien]

    try:
        ids = [int(x.strip()) for x in eingabe.split(',')]
        gueltige_ids = [kat[0] for kat in kategorien]
        ids = [id for id in ids if id in gueltige_ids]
        if not ids:
            print("Keine gültigen IDs eingegeben.")
            return []
        return ids
    except ValueError:
        print("Ungültiges Format. Bitte Zahlen mit Komma getrennt eingeben.")
        return []

# ------------------------------------------------------------------
# FRAGENANZAHL WÄHLEN (mit Sonderbehandlung für Kategorie 1)
# ------------------------------------------------------------------
def fragenanzahl_waehlen(kategorie_ids):
    conn = connect_db()
    cursor = conn.cursor()

    # Wenn Kategorie 1 (Gemischt) gewählt ist, alle anderen Kategorien verwenden
    if 1 in kategorie_ids:
        # Kategorie-IDs von 2 bis maximal vorhandene Kategorie (z.B. 15)
        cursor.execute("SELECT kategorie_id FROM kategorie WHERE kategorie_id != 1 ORDER BY kategorie_id")
        kategorie_ids_fuer_fragen = [row[0] for row in cursor.fetchall()]
    else:
        kategorie_ids_fuer_fragen = kategorie_ids

    if not kategorie_ids_fuer_fragen:
        print("Keine Fragenkategorien verfügbar.")
        cursor.close()
        conn.close()
        return [], 0, ""

    placeholders = ','.join(['%s'] * len(kategorie_ids_fuer_fragen))
    query_count = f"""
        SELECT COUNT(DISTINCT frage_id)
        FROM frage_mit_kategorie
        WHERE kategorie_id IN ({placeholders})
    """
    cursor.execute(query_count, kategorie_ids_fuer_fragen)
    total = cursor.fetchone()[0]

    if total == 0:
        print("Keine Fragen in den gewählten Kategorien vorhanden.")
        cursor.close()
        conn.close()
        return [], 0, ""

    print(f"\nEs sind {total} Fragen in den gewählten Kategorien verfügbar.")
    print("Wie viele Fragen möchtest du beantworten?")
    print("  'A' = Alle Fragen")
    print("  'U' = Unendlich (nach Durchlauf wiederholen)")
    print("  '20' = 20 Fragen (nur dieser Modus wird für den Highscore gewertet!)")

    while True:
        eingabe = input("Deine Wahl: ").strip().upper()
        if eingabe == 'A':
            limit = total
            break
        elif eingabe == 'U':
            limit = -1
            break
        elif eingabe == '20':
            if total >= 20:
                limit = 20
            else:
                print(f"⚠️ Es sind nur {total} Fragen verfügbar. Bitte wähle 'A' oder eine kleinere Anzahl.")
                continue
            break
        else:
            print("Ungültige Eingabe. Bitte wähle 'A', 'U' oder '20'.")

    # Fragen laden (über die tatsächlich zu nutzenden Kategorien)
    query_fragen = f"""
        SELECT DISTINCT frage_id, fragetext, erklaerung, typ, bezeichnung
        FROM frage_mit_kategorie
        WHERE kategorie_id IN ({placeholders})
        ORDER BY RAND()
    """
    if limit != -1:
        query_fragen += " LIMIT %s"
        cursor.execute(query_fragen, kategorie_ids_fuer_fragen + [limit])
    else:
        cursor.execute(query_fragen, kategorie_ids_fuer_fragen)

    fragen = cursor.fetchall()
    cursor.close()
    conn.close()
    return fragen, limit, eingabe

# ------------------------------------------------------------------
# STATISTIKEN
# ------------------------------------------------------------------
def statistik_menue():
    while True:
        print("\n--- STATISTIKEN ---")
        print("1. Highscores (alle Benutzer)")
        print("2. Meine Highscores")
        print("3. Meine Gesamtstatistik (Durchschnitt)")
        print("4. Zurück zum Hauptmenü")
        wahl = input("Auswahl: ").strip()
        if wahl == "1":
            highscore_anzeigen(alle=True)
        elif wahl == "2":
            highscore_anzeigen(alle=False)
        elif wahl == "3":
            persoenliche_statistik()
        elif wahl == "4":
            break
        else:
            print("Ungültige Eingabe.")

def highscore_anzeigen(alle=True):
    conn = connect_db()
    cursor = conn.cursor()
    if not alle:
        global current_user_id, current_user_name
        if current_user_id is None:
            auth = authentifiziere_benutzer()
            if not auth:
                cursor.close()
                conn.close()
                return
            benutzer_id, name = auth
        else:
            benutzer_id = current_user_id
            name = current_user_name
        where_clause = "AND b.benutzer_id = %s"
        params = [benutzer_id]
    else:
        where_clause = ""
        params = []

    query = f"""
        SELECT 
            b.kuerzel,
            COALESCE(k.bezeichnung, 'Mehrere Kategorien') AS bezeichnung,
            s.punkte,
            (SELECT COUNT(*) FROM detail d WHERE d.sitzung_id = s.sitzung_id) AS gesamt,
            ROUND((s.punkte / (SELECT COUNT(*) FROM detail d WHERE d.sitzung_id = s.sitzung_id)) * 100, 1) AS prozent,
            s.zeitpunkt
        FROM sitzung s
        JOIN benutzer b ON s.benutzer_id = b.benutzer_id
        LEFT JOIN kategorie k ON s.kategorie_id = k.kategorie_id
        WHERE (SELECT COUNT(*) FROM detail d WHERE d.sitzung_id = s.sitzung_id) = 20
        {where_clause}
        ORDER BY prozent DESC
        LIMIT 20
    """
    cursor.execute(query, params)
    results = cursor.fetchall()
    print("\n" + "=" * 70)
    print("🏆 HIGHSCORES (Bester Prozentsatz pro Benutzer und Modul)")
    print("=" * 70)
    print(f"{'Spieler':<10} {'Modul':<30} {'Punkte':<10} {'Prozent':<8} {'Datum':<16}")
    print("-" * 70)
    for row in results:
        kuerzel = row[0]
        modul_raw = row[1]
        modul = (modul_raw[:27] + '...') if len(modul_raw) > 30 else modul_raw
        punkte = f"{row[2]}/{row[3]}"
        prozent = f"{row[4]}%"
        datum = row[5].strftime("%d.%m.%Y %H:%M") if row[5] else ""
        print(f"{kuerzel:<10} {modul:<30} {punkte:<10} {prozent:<8} {datum:<16}")
    print("=" * 70)
    cursor.close()
    conn.close()

def persoenliche_statistik():
    global current_user_id, current_user_name
    if current_user_id is None:
        auth = authentifiziere_benutzer()
        if not auth:
            return
        benutzer_id, name = auth
    else:
        benutzer_id = current_user_id
        name = current_user_name
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT AVG(s.punkte / (SELECT COUNT(*) FROM detail d WHERE d.sitzung_id = s.sitzung_id) * 100)
        FROM sitzung s
        WHERE s.benutzer_id = %s
    """, (benutzer_id,))
    avg_total = cursor.fetchone()[0]
    avg_total = round(avg_total, 1) if avg_total else 0.0

    cursor.execute("""
        SELECT 
            COALESCE(k.bezeichnung, 'Mehrere Kategorien') AS bezeichnung,
            AVG(s.punkte / (SELECT COUNT(*) FROM detail d WHERE d.sitzung_id = s.sitzung_id) * 100) AS durchschnitt,
            COUNT(*) AS anzahl_spiele
        FROM sitzung s
        LEFT JOIN kategorie k ON s.kategorie_id = k.kategorie_id
        WHERE s.benutzer_id = %s
        GROUP BY s.kategorie_id
        ORDER BY durchschnitt DESC
    """, (benutzer_id,))
    stats = cursor.fetchall()
    print("\n" + "=" * 50)
    print(f"📊 PERSÖNLICHE STATISTIK FÜR {name}")
    print("=" * 50)
    print(f"Gesamtdurchschnitt über alle Spiele: {avg_total}%")
    print("\nDurchschnitt pro Modul:")
    print("-" * 50)
    for row in stats:
        modul = row[0]
        avg = round(row[1], 1) if row[1] else 0.0
        spiele = row[2]
        print(f"{modul:<35} {avg}%  ({spiele} Spiele)")
    print("=" * 50)
    cursor.close()
    conn.close()

# ------------------------------------------------------------------
# QUIZ STARTEN
# ------------------------------------------------------------------
def quiz_starten():
    conn = connect_db()
    cursor = conn.cursor()

    try:
        benutzer_id, name, kuerzel = ensure_login(conn, cursor)

        # --- Kategorie(n) wählen ---
        kategorie_ids = waehle_kategorie_bereich()
        if not kategorie_ids:
            log_event("Quiz-Start abgebrochen (keine Kategorie)", username=kuerzel)
            return

        # --- Fragenanzahl wählen (kümmert sich um Sonderfall Kategorie 1) ---
        fragen, limit, eingabe_modus = fragenanzahl_waehlen(kategorie_ids)
        if not fragen:
            log_event("Quiz-Start abgebrochen (keine Fragen)", username=kuerzel)
            return

        # Highscore-Bedingungen prüfen
        highscore_tauglich = (eingabe_modus == '20' and len(kategorie_ids) == 1 and kategorie_ids[0] != 1)
        if eingabe_modus == '20' and not highscore_tauglich:
            print("\n⚠️ Hinweis: Highscore wird nur bei Auswahl genau EINER Kategorie (außer Gemischt) gewertet.")
        elif highscore_tauglich:
            print("\n✅ Dieser Durchlauf ist Highscore-fähig (20 Fragen, eine Kategorie).")

        kat_str = ','.join(str(x) for x in kategorie_ids)
        modus = "unendlich" if limit == -1 else f"{limit} Fragen"
        log_event("Quiz gestartet", username=kuerzel, details=f"Kategorien: {kat_str}, Modus: {modus}")

        # --- Session anlegen ---
        kategorie_ref = kategorie_ids[0] if len(kategorie_ids) == 1 else None
        cursor.execute(
            "INSERT INTO sitzung (benutzer_id, kategorie_id, punkte) VALUES (%s, %s, 0)",
            (benutzer_id, kategorie_ref)
        )
        sitzung_id = cursor.lastrowid
        conn.commit()

        # --- Quiz durchlaufen ---
        punkte = 0
        fragen_nummer = 1
        abgebrochen = False
        fragen_pool = list(fragen)

        while True:
            if limit == -1 and fragen_nummer > len(fragen_pool):
                random.shuffle(fragen_pool)
                fragen_nummer = 1
                print("\n--- Alle Fragen beantwortet. Neuer Durchlauf ---")

            if limit == -1:
                frage = fragen_pool[fragen_nummer - 1]
            else:
                if fragen_nummer > len(fragen):
                    break
                frage = fragen[fragen_nummer - 1]

            frage_id = frage[0]
            fragetext = frage[1]
            erklaerung = frage[2]
            frage_typ = frage[3]          # 'MC' oder 'FT'
            kategorie_bezeichnung = frage[4]

            print(f"\n--- Frage {fragen_nummer}" + (f"/{len(fragen)}" if limit != -1 else " ---"))
            print(f"[{kategorie_bezeichnung}]")
            print(fragetext)

            cursor.execute(
                "SELECT antwort_id, antworttext, ist_korrekt FROM antwort WHERE frage_id = %s ORDER BY RAND()",
                (frage_id,)
            )
            antworten = cursor.fetchall()

            if frage_typ == 'FT':
                # Freitext: alle geladenen Antworten sind korrekte Varianten
                korrekte_antworten = [a[1] for a in antworten]
                while True:
                    eingabe = input("Deine Antwort (Freitext, 'exit' zum Abbrechen): ").strip()
                    if eingabe == "":
                        print("Bitte gib eine Antwort ein.")
                        continue
                    break
                if eingabe.lower() in ('exit', 'q'):
                    abgebrochen = True
                    break

                war_korrekt = any(eingabe.lower() == k.lower() for k in korrekte_antworten)
                if war_korrekt:
                    print("✅ Richtig!")
                    punkte += 1
                else:
                    loesungen = ", ".join(korrekte_antworten)
                    print(f"❌ Falsch. Mögliche Lösungen: {loesungen}")
            else:
                # Multiple-Choice
                optionen = {}
                for i, antwort in enumerate(antworten):
                    nummer = i + 1
                    optionen[str(nummer)] = {
                        'text': antwort[1],
                        'korrekt': antwort[2]
                    }
                    print(f"{nummer}: {antwort[1]}")
                while True:
                    wahl = input("Deine Wahl (1/2/3/4, 'exit' zum Abbrechen): ").strip()
                    if wahl == "":
                        print("Bitte gib eine Nummer ein.")
                        continue
                    if wahl.lower() in ('exit', 'q'):
                        abgebrochen = True
                        break
                    if wahl in optionen:
                        break
                    print("Bitte 1, 2, 3 oder 4 eingeben.")
                if abgebrochen:
                    break
                war_korrekt = optionen[wahl]['korrekt']
                if war_korrekt:
                    print("✅ Richtig!")
                    punkte += 1
                else:
                    richtige = [a['text'] for a in optionen.values() if a['korrekt']]
                    print(f"❌ Falsch. Richtig wäre: {', '.join(richtige)}")

            if erklaerung:
                print(f"ℹ️ {erklaerung}")

            cursor.execute(
                "INSERT INTO detail (sitzung_id, frage_id, war_korrekt) VALUES (%s, %s, %s)",
                (sitzung_id, frage_id, war_korrekt)
            )
            conn.commit()

            fragen_nummer += 1

            if limit == -1:
                weiter = input("Weiter? (Enter für ja, 'exit' zum Beenden): ").strip().lower()
                if weiter in ('exit', 'q'):
                    abgebrochen = True
                    break

        if abgebrochen:
            print("\n⚠️ Quiz abgebrochen. Diese Sitzung wird nicht gewertet.")
            cursor.execute("DELETE FROM detail WHERE sitzung_id = %s", (sitzung_id,))
            cursor.execute("DELETE FROM sitzung WHERE sitzung_id = %s", (sitzung_id,))
            conn.commit()
            log_event("Quiz abgebrochen", username=kuerzel, details=f"Punkte: {punkte}/{fragen_nummer-1}")
        else:
            cursor.execute(
                "UPDATE sitzung SET punkte = %s WHERE sitzung_id = %s",
                (punkte, sitzung_id)
            )
            conn.commit()
            gesamt_fragen = len(fragen) if limit != -1 else fragen_nummer - 1
            prozent = (punkte / gesamt_fragen) * 100
            print("\n" + "=" * 40)
            print(f"QUIZ BEENDET! Du hast {punkte} von {gesamt_fragen} Punkten erreicht.")
            print(f"Das entspricht {prozent:.1f}%.")
            if highscore_tauglich and not abgebrochen:
                print("✅ Dieses Ergebnis wurde für den Highscore gespeichert.")
            print("=" * 40)
            log_event("Quiz beendet", username=kuerzel, details=f"Punkte: {punkte}/{gesamt_fragen} ({prozent:.1f}%)")

    except Exception as e:
        log_event("Fehler in quiz_starten", username="SYSTEM", details=str(e))
        print("\n❌ Ein unerwarteter Fehler ist aufgetreten. Das Quiz wird beendet.")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# ------------------------------------------------------------------
# ANLEITUNG
# ------------------------------------------------------------------
def zeige_anleitung():
    print("\n" + "=" * 60)
    print("FISI QUIZ – BEDIENUNGSANLEITUNG")
    print("=" * 60)
    print("""
1. ANMELDUNG
   - Gib dein persönliches Kürzel und Passwort ein.
   - Bei erstmaliger Nutzung wirst du aufgefordert, ein Passwort zu vergeben.
   - Nach erfolgreicher Anmeldung bleibst du für die gesamte Sitzung eingeloggt.

2. QUIZ STARTEN
   - Wähle einen Kategoriebereich:
       '1' = Gemischt (alle Fragen)
       '2' = BFW-Module (Unterrichtsinhalte)
       '3' = Prüfungsvorbereitung (AP I / AP II)
   - Im Untermenü kannst du einzelne Module/Kategorien auswählen (z. B. '2,4,7').
   - Bestimme die Anzahl der Fragen:
       'A' = alle verfügbaren Fragen
       'U' = unendlicher Modus (Fragen wiederholen sich)
       '20' = 20 Fragen (nur dieser Modus und genau EINE Kategorie führen zu einem Highscore-Eintrag!)
   - Beantworte die Fragen durch Eingabe der Nummer (1–4) oder Freitext.
   - Mit 'exit' kannst du jederzeit abbrechen (nicht gewertet).

3. STATISTIKEN
   - Highscores: Zeigt die besten 20-Fragen-Runden aller oder nur deine.
   - Persönliche Statistik: Dein Gesamtdurchschnitt über alle gespielten Runden.

4. BEENDEN
   - Menüpunkt '6' im Hauptmenü beendet das Programm und trennt die SSH-Verbindung.

Bei Problemen wende dich an den Administrator.
""")
    print("=" * 60)
    input("\nDrücke Enter, um zum Hauptmenü zurückzukehren...")

# ------------------------------------------------------------------
# HAUPTMENÜ
# ------------------------------------------------------------------
def hauptmenue():
    while True:
        total = gesamtanzahl_fragen()  # Gesamtzahl aller Fragen für Gemischt
        print("\n" + "=" * 40)
        print("       FISI QUIZ - PRÜFUNGSVORBEREITUNG")
        print("=" * 40)
        print(f"1. Gemischt (alle Fragen)  [{total} Fragen]")
        print("2. BFW-Module (Unterrichtsinhalte)")
        print("3. Prüfungsvorbereitung (AP I / AP II)")
        print("4. Statistiken")
        print("5. Anleitung")
        print("6. Beenden")
        wahl = input("Auswahl: ").strip()
        if wahl == "1":
            quiz_starten_mit_kategorie([1])
        elif wahl == "2":
            kategorie_ids = waehle_unterkategorien(2, 9, "BFW-Module")
            if kategorie_ids:
                quiz_starten_mit_kategorie(kategorie_ids)
        elif wahl == "3":
            kategorie_ids = waehle_unterkategorien(10, 15, "Prüfungsvorbereitung")
            if kategorie_ids:
                quiz_starten_mit_kategorie(kategorie_ids)
        elif wahl == "4":
            statistik_menue()
        elif wahl == "5":
            zeige_anleitung()
        elif wahl == "6":
            print("Auf Wiedersehen!")
            break
        else:
            print("Ungültige Eingabe.")

def quiz_starten_mit_kategorie(kategorie_ids):
    global _preset_kategorie_ids
    _preset_kategorie_ids = kategorie_ids
    original_waehle = waehle_kategorie_bereich
    globals()['waehle_kategorie_bereich'] = lambda: _preset_kategorie_ids
    quiz_starten()
    globals()['waehle_kategorie_bereich'] = original_waehle

# ------------------------------------------------------------------
# START
# ------------------------------------------------------------------
if __name__ == "__main__":
    try:
        hauptmenue()
    except KeyboardInterrupt:
        print("\n\nProgramm durch Benutzer beendet.")
        log_event("Programm durch KeyboardInterrupt beendet")
    except Exception as e:
        log_event("Unbehandelter Fehler im Hauptprogramm", details=str(e))
        print("Ein schwerwiegender Fehler ist aufgetreten. Bitte Administrator kontaktieren.")