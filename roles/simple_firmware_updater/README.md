# Rôle Ansible : simple_firmware_updater

## Description

Le rôle `simple_firmware_updater` est une version simplifiée du processus de mise à jour firmware pour les switches Aruba AOS-CX. Il offre un workflow linéaire en 7 étapes sans les fonctionnalités avancées du rôle `firmware_updater` standard.

## Fonctionnalités

- ✅ Vérification du modèle de switch
- ✅ Validation de l'existence du firmware sur le serveur repository
- ✅ Comparaison des versions (mise à jour uniquement si version supérieure)
- ✅ Sauvegarde automatique de la configuration
- ✅ Upload du firmware sur la partition primary
- ✅ Redémarrage contrôlé avec timeout de 15 minutes
- ✅ Validation post-redémarrage
- ✅ Mode dry-run pour simuler la mise à jour sans modifications

## Prérequis

- Ansible 2.9+
- Collection `arubanetworks.aoscx` installée
- Accès SSH configuré sur les switches
- Serveur repository accessible

### Pour l'accès au serveur repository

Le rôle doit pouvoir se connecter au serveur repository pour vérifier les firmwares et transférer les sauvegardes.

**Option 1 : Authentification par mot de passe (nécessite sshpass)**
```bash
# Installation de sshpass
sudo yum install sshpass    # RedHat/CentOS
sudo apt install sshpass    # Debian/Ubuntu
```

**Option 2 : Authentification par clé SSH (recommandé)**
```bash
ssh-copy-id deploy@votre-serveur-repository
```

## Variables requises

| Variable | Description | Exemple |
|----------|-------------|---------|
| `switch_model` | Modèle du switch attendu | `"6100"` |
| `firmware_filename` | Nom du fichier firmware | `"ArubaOS-CX_6100-6000_10_13_1120.swi"` |

## Variables optionnelles

| Variable | Description | Défaut |
|----------|-------------|---------|
| `dry_run` | Mode simulation sans modifications | `false` |
| `force_backup_in_dryrun` | Forcer la sauvegarde même en mode dry-run | `false` |
| `firmware_source_type` | Type de source du firmware ("local" ou "remote") | `"local"` |
| `local_firmware_path` | Chemin local où se trouve le firmware | `"/firmware/{{ switch_model }}"` |
| `repository_server` | Serveur de stockage (local ou HTTP) | `"backup.example.com"` |
| `repository_path` | Chemin sur le serveur repository (pour HTTP) | `"/firmware"` |
| `backup_enabled` | Activer la sauvegarde de configuration | `true` |
| `backup_path` | Chemin de sauvegarde | `"/backups/network/aruba/config_backups"` |
| `backup_requires_sudo` | Le transfert de sauvegarde nécessite sudo | `true` |
| `upload_timeout` | Timeout pour l'upload (secondes) | `600` |
| `reboot_timeout` | Timeout pour le redémarrage (secondes) | `900` |

## Utilisation

### Playbook minimal

```yaml
- name: Mise à jour firmware simple
  hosts: switches_aruba_6100
  gather_facts: no
  roles:
    - role: simple_firmware_updater
      vars:
        switch_model: "6100"
        firmware_filename: "ArubaOS-CX_6100-6000_10_13_1120.swi"
```

### Playbook avec source locale (défaut)

```yaml
- name: Mise à jour firmware depuis fichier local
  hosts: switches_aruba
  gather_facts: no
  vars:
    firmware_source_type: "local"
    local_firmware_path: "/opt/aruba_reports/firmware"
    repository_server: "s-ansible-1"  # Serveur où se trouve le fichier
  roles:
    - role: simple_firmware_updater
      vars:
        switch_model: "6000"
        firmware_filename: "ArubaOS-CX_6000_10_13_1120.swi"
```

### Playbook avec source HTTP distante

```yaml
- name: Mise à jour firmware depuis serveur HTTP
  hosts: switches_aruba
  gather_facts: no
  vars:
    firmware_source_type: "remote"
    repository_server: "firmware.monentreprise.com"
    repository_path: "/aruba/firmwares"
    backup_path: "/aruba/backups"
  roles:
    - role: simple_firmware_updater
      vars:
        switch_model: "6300"
        firmware_filename: "ArubaOS-CX_6300M_10_13_1020.swi"
        upload_timeout: 1200
        reboot_timeout: 1200
```

### Mode Dry-Run

Le mode dry-run permet de simuler la mise à jour sans effectuer aucune modification :

```yaml
- name: Mise à jour firmware en mode dry-run
  hosts: switches_aruba
  gather_facts: no
  roles:
    - role: simple_firmware_updater
      vars:
        switch_model: "6100"
        firmware_filename: "ArubaOS-CX_6100-6000_10_13_1120.swi"
        dry_run: true
```

Ou via la ligne de commande :

```bash
# Mode dry-run via extra vars
ansible-playbook update_simple.yml -e "dry_run=true"
```

### Sauvegarde de configuration sans mise à jour

**IMPORTANT** : Il est fortement recommandé de tester et valider la sauvegarde avant toute mise à jour firmware.

**Note sur les permissions** : Les opérations de sauvegarde nécessitent des privilèges sudo sur le serveur repository. Le rôle utilise automatiquement les variables suivantes depuis votre vault :
- `repository_user` : Utilisateur pour se connecter au serveur repository
- `repository_password` : Mot de passe de connexion
- `repository_become_password` : Mot de passe sudo/become

#### Méthode 1 : Utiliser les tags (recommandé)

```bash
# Vérifications ET sauvegarde uniquement (sans mise à jour)
ansible-playbook -i inventory/switches.yml simple_firmware_update.yml \
  -e "switch_model=6000" \
  -e "firmware_filename=ArubaOS-CX_6100-6000_10_13_1120.swi" \
  --tags "check,backup" \
  --ask-vault-pass

# Sauvegarde uniquement (sans vérifications)
ansible-playbook -i inventory/switches.yml simple_firmware_update.yml \
  --tags "backup" \
  --ask-vault-pass
```

#### Méthode 2 : Mode dry-run avec sauvegarde forcée

```bash
# Mode dry-run mais effectue réellement la sauvegarde
ansible-playbook -i inventory/switches.yml simple_firmware_update.yml \
  -e "switch_model=6000" \
  -e "firmware_filename=ArubaOS-CX_6100-6000_10_13_1120.swi" \
  -e "dry_run=true" \
  -e "force_backup_in_dryrun=true" \
  --ask-vault-pass
```

#### Méthode 3 : Test direct avec include de tâche

Pour tester uniquement la sauvegarde, vous pouvez utiliser le playbook existant avec uniquement le tag backup :

```bash
# Test de sauvegarde uniquement sur un switch spécifique
ansible-playbook -i inventory/switches.yml simple_firmware_update.yml \
  -e "switch_model=6000" \
  -e "firmware_filename=ArubaOS-CX_6100-6000_10_13_1120.swi" \
  --tags "backup" \
  --limit "switch01" \
  --ask-vault-pass
```

#### Option : Sauvegarde locale uniquement (sans sudo)

Si vous ne souhaitez pas fournir le mot de passe sudo, vous pouvez désactiver le transfert automatique :

```bash
# Sauvegarde locale uniquement, sans transfert vers le serveur repository
ansible-playbook -i inventory/switches.yml simple_firmware_update.yml \
  -e "switch_model=6000" \
  -e "firmware_filename=ArubaOS-CX_6100-6000_10_13_1120.swi" \
  -e "backup_requires_sudo=false" \
  --tags "backup" \
  --ask-vault-pass
```

Les fichiers de sauvegarde seront créés localement sur le contrôleur Ansible et pourront être transférés manuellement ultérieurement.

### Utilisation avec tags

```bash
# Vérifications uniquement (sans modification)
ansible-playbook update_simple.yml --tags "check"

# Sauvegarde uniquement
ansible-playbook update_simple.yml --tags "backup"

# Upload et redémarrage uniquement (dangereux!)
ansible-playbook update_simple.yml --tags "upload,reboot"

# Validation uniquement
ansible-playbook update_simple.yml --tags "validate"
```

## Workflow détaillé

### 1. Vérification du modèle (`check_model.yml`)
- Récupère le modèle réel du switch via `show system`
- Compare avec le modèle attendu
- Arrête le processus si non concordance

### 2. Vérification du firmware (`check_firmware.yml`)
- Vérifie l'existence du fichier sur le serveur repository
- Récupère la taille du fichier
- Valide l'accessibilité HTTP/HTTPS

### 3. Comparaison des versions (`compare_versions.yml`)
- Extrait la version actuelle de la partition primary
- Extrait la version cible du nom du firmware
- Arrête si la version cible n'est pas supérieure

### 4. Sauvegarde (`backup_config.yml`)
- Récupère la configuration via `show running-config`
- Sauvegarde localement puis transfère au serveur repository
- Nomme le fichier avec horodatage

### 5. Upload du firmware (`upload_firmware.yml`)
- Upload le firmware sur la partition primary uniquement
- Utilise le module `aoscx_upload_firmware`
- Timeout configurable (défaut: 10 minutes)

### 6. Redémarrage (`reboot_switch.yml`)
- Configure le boot sur la partition primary
- Redémarre le switch
- Attend la reconnexion (timeout: 15 minutes)

### 7. Validation (`validate_version.yml`)
- Vérifie la version après redémarrage
- Compare avec la version attendue
- Nettoie les fichiers temporaires

## Différences avec le rôle `firmware_updater`

| Fonctionnalité | `simple_firmware_updater` | `firmware_updater` |
|----------------|---------------------------|-------------------|
| Gestion multi-partition | ❌ Primary uniquement | ✅ Primary/Secondary |
| Sélection auto du firmware | ❌ Manuel | ✅ Par modèle |
| Rollback automatique | ❌ | ✅ |
| Stratégies d'installation | ❌ | ✅ Multiple |
| Métriques détaillées | ❌ | ✅ |
| Mode dry-run | ✅ Simplifié | ✅ Complet |
| Rapport HTML | ❌ | ✅ |

## Structure des fichiers

```
roles/simple_firmware_updater/
├── defaults/main.yml      # Variables par défaut
├── vars/main.yml          # Variables internes
├── tasks/
│   ├── main.yml          # Workflow principal
│   ├── check_model.yml   # Vérification modèle
│   ├── check_firmware.yml # Vérification firmware
│   ├── compare_versions.yml # Comparaison versions
│   ├── backup_config.yml # Sauvegarde config
│   ├── upload_firmware.yml # Upload firmware
│   ├── reboot_switch.yml # Redémarrage
│   └── validate_version.yml # Validation finale
└── README.md             # Cette documentation
```

## Gestion des erreurs

Le rôle s'arrête immédiatement en cas d'erreur à n'importe quelle étape :
- Modèle non concordant
- Firmware introuvable
- Version déjà à jour
- Échec de sauvegarde
- Timeout d'upload
- Timeout de redémarrage
- Version finale incorrecte

## Messages en français

Tous les messages utilisateur sont en français et configurables via les variables `msg_*` dans `defaults/main.yml`.

## Exemples de sortie

### Succès
```
TASK [simple_firmware_updater : Afficher les informations de mise à jour] ***
ok: [switch-01] => {
    "msg": "=== MISE À JOUR FIRMWARE SIMPLIFIÉE ===\nSwitch: switch-01\nModèle attendu: 6100\nFirmware: ArubaOS-CX_6100-6000_10_13_1120.swi\n====================================="
}

[...]

TASK [simple_firmware_updater : Afficher le résumé de la mise à jour] ***
ok: [switch-01] => {
    "msg": "=== MISE À JOUR TERMINÉE AVEC SUCCÈS ===\nSwitch: switch-01\nVersion installée: 10.13.1120\n========================================"
}
```

### Échec (version déjà à jour)
```
TASK [simple_firmware_updater : Vérifier si la mise à jour est nécessaire] ***
ok: [switch-01] => {
    "msg": "INFO: La version actuelle est déjà égale ou supérieure à la version cible"
}

PLAY RECAP *********************************************************************
switch-01 : ok=5 changed=0 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

### Mode Dry-Run
```
TASK [simple_firmware_updater : Vérifier le mode dry-run] ***
ok: [switch-01] => {
    "msg": "MODE DRY-RUN ACTIVÉ - Aucune modification ne sera effectuée"
}

[...]

TASK [simple_firmware_updater : Afficher les actions qui seraient effectuées (DRY-RUN)] ***
ok: [switch-01] => {
    "msg": "=== ACTIONS QUI SERAIENT EFFECTUÉES ===\n✓ Upload du firmware ArubaOS-CX_6100-6000_10_13_1120.swi sur la partition primary\n✓ Redémarrage du switch sur la nouvelle version\n✓ Validation de la version après redémarrage\n======================================"
}

TASK [simple_firmware_updater : Afficher le résumé du dry-run] ***
ok: [switch-01] => {
    "msg": "=== DRY-RUN TERMINÉ ===\nSwitch: switch-01\nVersion actuelle: 10.13.1000\nVersion cible: 10.13.1120\nAucune modification effectuée\n======================"
}
```

## Dépannage

### Erreur "you must install the sshpass program"

Cette erreur apparaît lors de la connexion SSH au serveur repository avec un mot de passe.

**Solutions :**

1. **Installer sshpass** (solution rapide) :
   ```bash
   sudo yum install sshpass    # RedHat/CentOS
   sudo apt install sshpass    # Debian/Ubuntu
   ```

2. **Utiliser des clés SSH** (solution recommandée) :
   ```bash
   # Générer une clé si nécessaire
   ssh-keygen -t rsa -b 4096
   
   # Copier la clé sur le serveur repository
   ssh-copy-id deploy@10.20.3.11
   
   # Retirer repository_password du vault
   ansible-vault edit group_vars/all/vault.yml
   ```

### Autres problèmes

Pour toute question ou problème, consultez d'abord les logs avec `-vvv` :

```bash
ansible-playbook update_simple.yml -vvv
```

## Licence

Ce rôle fait partie du projet aruba-manager et suit la même licence.