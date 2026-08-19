# Original User Request

## 2026-08-19T11:03:51Z

Refonte visuelle et ergonomique majeure de Galactic Focus dans un style Cyberpunk Synthwave / Nova Space Command Center haute fidélité, enrichi en néons vifs (cyan laser, violet synthwave, rose néon, ambre et vert matrix), avec typographie futuriste soignée, micro-animations réactives (survol, clic, pulsation de propulsion), écrans de bord tactiques et suppression de tout bouton inutile.

Working directory: c:\Users\AURUMPC\Documents\programmation\appProduct
Integrity mode: demo

## Requirements

### R1. Direction Artistique Cyberpunk Synthwave & Nova Space Control
- Palette de couleurs vibrante et contrastée :
  - Fond cosmique profond : `#030712` / `#060B1A`
  - Cartes et panneaux : `#0A1329` avec reflets néon et bordures lumineuses `#182C5A`
  - Accents lumineux vifs : **Laser Cyan** (`#00F0FF`), **Synthwave Purple / Violet Kyber** (`#A855F7`), **Neon Pink / Magenta** (`#F43F5E` / `#EC4899`), **Solar Amber** (`#F59E0B`), **Hyper Green** (`#10B981`).
- Typographie soignée : Titres géométriques nets (style Orbitron / Eurostile), valeurs numériques en grand format contrasté, suppression de la police terminal brute Consolas et des crochets/symboles superflus.
- Épuration totale : Zéro bouton parasite ou doublon, interface directe et focalisée sur le vol spatial et les missions.

### R2. Animations & Micro-Interactions Dynamiques
- **Cartes interactives (`on_hover`)** : Éclairage progressif de la bordure avec halo néon magenta/cyan et légère élévation de l'ombre portée.
- **Boutons biseautés interactifs** : Animation d'agrandissement doux (`scale: 1.02`), surbrillance néon et retour tactile au clic.
- **Compte à rebours animé** : Effets de pulsation lumineuse des anneaux de propulsion et du chronomètre lors des phases d'Ignition, Hyperdrive et Overdrive.
- **Capsule Switcher Flottant** : Sélecteur de filtres et de durées en pilule animée avec transitions fluides.

### R3. Visualisations Télémétriques & Écrans Tactiques
- Intégration harmonieuse des écrans de contrôle (Oscilloscope Warp ambre/violet et Radar orbital cyan/vert) avec encadrements soignés sans aucun bug visuel.
- Affichage clair du registre d'escadron du jour et des badges de mission.

### R4. Structure Ergonomique des 3 Écrans Essentiels
- **Cockpit (Pont de Commandement)** : Sélecteur de vaisseau actif, sélection de durée, grand HUD central avec compte à rebours immersif, moniteurs latéraux et radar du jour.
- **Missions (Centre de Directives)** : Dossiers de missions globales et spécifiques avec jauges de progression néon et filtres capsules.
- **Hangar (Spacedock & Flotte)** : Fiches techniques des vaisseaux armés, Vaisseau Amiral (travail global), archives au rebut et carnet d'entretien exportable en CSV.

## Verification Resources

- Suite de tests unitaires et d'intégration existante : `galactic_focus/tests/test_galactic_core.py` (14 tests).
- Validation de lancement sans exception via script de test autonome.
- Script de compilation Windows PyInstaller : `main.py` -> `GalacticFocus.exe`.

## Acceptance Criteria

### Rendu Visuel & Expérience Utilisateur
- [ ] Le design est vibrant, moderne et riche en couleurs cyberpunk synthwave (cyan, violet, rose, ambre).
- [ ] Les cartes et boutons réagissent immédiatement et avec fluidité au survol de la souris (`on_hover`) et au clic.
- [ ] Le compte à rebours pulse de manière dynamique lors du vol.
- [ ] La typographie est moderne, lisible et parfaitement calibrée sur tous les écrans sans encombrement.
- [ ] Toutes les images et écrans CRT s'affichent impeccablement sans superposition ni artefact.

### Tests & Compilation
- [ ] Les 14 tests unitaires et d'intégration s'exécutent avec 100% de succès (`python -m unittest discover -s galactic_focus/tests`).
- [ ] Le binaire autonome `GalacticFocus.exe` est généré à la racine avec son icône et se lance instantanément.
