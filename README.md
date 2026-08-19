# 🪐 Galactic Focus — Nova Command Center V5.0

Application de productivité ultra-rapide gamifiée dans un univers spatial Cyberpunk Synthwave & Nova Command Center.

Développée en **Python avec Flet (Flutter)**, elle fonctionne en exécutable **natif Windows** ultra-fluide et s'exporte instantanément sur le **Web / PWA**.

---

## 🎯 Fonctionnalités Principales

1. **Cockpit & Pont de Commandement** :
   - Sélection du vaisseau appareillé et choix de durée (15m, 20m, 25m, 30m, 45m, 60m).
   - HUD central avec compte à rebours immersif, anneaux de propulsion et phases de vol (Ignition, Hyperdrive, Overdrive).
   - Validation automatique dès `00:00` sans interruption du flow, puis décompte en Overdrive.
   - Radar d'escadron journalier et badges d'activité.

2. **Centre de Directives & Missions** :
   - Missions globales (affectées au Vaisseau Amiral) et missions spécifiques par vaisseau.
   - Objectifs horaires, jauges de progression néon en temps réel et badges d'échéance dynamiques (Aujourd'hui, Demain, J-X, En retard).
   - Décollage direct en 1 clic vers une mission ciblée.

3. **Spacedock & Hangar de Flotte** :
   - Gestion de la flotte en service actif (personnalisation, couleurs néon, icônes).
   - Protection du Vaisseau Amiral (indestructible et inamovible).
   - Baie d'appareillage, zone d'archives (mise au rebut / restauration / suppression définitive).
   - Carnet d'entretien et registre de vol exportable en **CSV UTF-8-BOM** en 1 clic.

---

## 🚀 Démarrage Rapide

### 1. Installation des Dépendances
```bash
pip install -r requirements.txt
```

### 2. Lancement en Mode Desktop
```bash
python main.py
```

### 3. Lancement en Mode Web / Navigateur
```bash
flet run main.py --web
```

### 4. Compilation du Binaire Windows (.exe)
```bash
build_exe.bat
```

---

## 🧪 Tests Automatisés

```bash
python -m unittest discover -s galactic_focus/tests -v
```
*(51 tests unitaires couvrant les modèles, le moteur temporel, la persistance, les invariants et les scénarios de stress)*.

---

## 📁 Architecture du Projet

```text
galactic_focus/
├── main.py                  # Point d'entrée Flet (Desktop / Web)
├── data.json                # Stockage local JSON 100% hors-ligne
├── requirements.txt         # Dépendances du projet (Flet, Pillow, PyInstaller)
├── LICENSE                  # Licence Apache 2.0
├── NOTICE                   # Mentions de copyright et attribution
├── core/
│   ├── models.py            # Modèles Ship, Mission, FocusSession, DailyFleetSummary
│   ├── storage.py           # Persistance locale JSON, résolutions automatiques & exports CSV
│   └── timer_engine.py      # Moteur temporel précis & machine à états (Idle, Ignition, Focusing, Overtime)
├── ui/
│   ├── theme.py             # Thème Cyberpunk Synthwave (Néons, cartes interactives, boutons biseautés)
│   ├── cockpit_view.py      # Pont de commandement : HUD de vol, sélecteurs, radar d'escadron
│   ├── missions_view.py     # Centre de directives : Cartes de missions, jauges néon, filtres
│   └── hangar_view.py       # Spacedock : Flotte active, archives, carnet d'entretien
├── assets/                  # Arrière-plans atmosphériques et icônes
└── tests/                   # 51 tests unitaires et d'intégration
```

---

## 🔒 100% Local, Privé & Sans Abonnement
Toutes les données sont conservées localement dans `data.json`. Aucun compte externe, aucun tracking, aucun cloud obligatoire.

---

## 📄 Licence

Ce projet est sous licence **Apache License 2.0** — consultez le fichier [`LICENSE`](LICENSE) et [`NOTICE`](NOTICE) pour plus de détails.
