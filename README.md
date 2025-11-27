# Keylogger Loris et Mathys

Ce projet contient un **keylogger Windows (client)** et un **serveur de
commande + dashboard web (C2)** permettant :

-   de recevoir les logs clavier en temps réel ;
-   de lancer / arrêter le keylogger via un port de commande ;
-   de visualiser les logs dans une interface web.

------------------------------------------------------------------------

## Structure du projet

    .
    ├── keylogger.py      # Client Windows (pynput)
    ├── server.py         # Serveur Linux (C2 + interface web)
    └── README.md

------------------------------------------------------------------------

##  Installation

### **Côté serveur (Linux)**

Dépendances :

``` bash
pip install flask
```

Lancer le serveur :

``` bash
python3 server.py
```

Le serveur démarre : - un socket pour les logs (port **12345**) - un
socket pour les commandes (port **12346**) - une interface web

------------------------------------------------------------------------

### **Côté client (Windows)**

Installer pynput :

``` powershell
pip install pynput
```

Lancer :

``` powershell
python keylogger.py
```
