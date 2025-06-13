# Rôle Ansible: firmware_updater

Ce rôle permet de mettre à jour le firmware des commutateurs Aruba AOS-CX de manière sécurisée et automatisée. Il gère l'upload, le redémarrage, la vérification et le rollback en cas d'échec.

## Prérequis

- Ansible 2.10 ou supérieur
- Collection Ansible Aruba AOS-CX : `arubanetworks.aoscx`
- Modules Python requis sur le contrôleur Ansible :
  - `pyaoscx>=2.6.0`
  - `jmespath`
- API REST activée sur les switches AOS-CX
- Serveur de dépôt externe configuré (pour sauvegardes et rapports)

## Fonctionnalités

### Workflow sécurisé de mise à jour
1. **Vérification des prérequis** : connectivité, espace disque, permissions
2. **Collecte de l'état actuel** : versions des partitions, configuration
3. **Stratégie intelligente** : choix automatique de la partition optimale
4. **Sauvegarde** : configuration actuelle avant modification
5. **Upload sécurisé** : firmware vers la partition cible
6. **Redémarrage contrôlé** : avec surveillance et timeouts adaptés
7. **Vérification complète** : version, fonctionnalité, stabilité
8. **Rollback automatique** : en cas d'échec de vérification

### Gestion intelligente des partitions
- **Stratégie automatique** : choix de la partition optimale
- **Protection rollback** : conservation d'une version fonctionnelle
- **Dual partition** : support complet du système de partitions AOS-CX

### Robustesse et fiabilité
- **Timeouts adaptatifs** : selon le modèle de switch
- **Retry automatique** : sur erreurs temporaires
- **Vérifications multiples** : à chaque étape critique
- **Gestion d'erreurs** : récupération intelligente

## Variables

### Variables obligatoires

| Variable | Description |
|----------|-------------|
| `firmware_file_path` | Chemin vers le fichier firmware (.swi) |
| `target_firmware_version` | Version cible du firmware |
| `repository_server` | Serveur de dépôt pour sauvegardes et rapports |

### Variables de configuration principales

| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| `partition_strategy` | Stratégie de partition (auto, primary, secondary) | `auto` |
| `upload_method` | Méthode d'upload (local, remote) | `local` |
| `backup_config` | Sauvegarder la configuration | `true` |
| `verify_post_update` | Vérifier après la mise à jour | `true` |
| `rollback_on_failure` | Rollback automatique si échec | `true` |
| `force_update` | Forcer même si version déjà installée | `false` |

### Variables de timing et retry

| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| `max_upload_time` | Timeout upload (secondes) | `1800` |
| `max_reboot_time` | Timeout reboot (secondes) | `600` |
| `post_reboot_wait` | Attente post-reboot (secondes) | `180` |
| `max_retries` | Nombre max de tentatives | `3` |
| `retry_delay` | Délai entre tentatives (secondes) | `30` |

### Variables de dépôt et sauvegarde

| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| `repository_path` | Chemin sur le serveur de dépôt | `/backups/firmware` |
| `repository_port` | Port du serveur de dépôt | `22` |
| `backup_method` | Méthode de sauvegarde (local, tftp) | `local` |
| `keep_backup_count` | Nombre de sauvegardes à conserver | `2` |

## Utilisation

### Exemple de playbook

```yaml
---
- name: Update Aruba switches firmware
  hosts: switches_aruba
  gather_facts: false
  vars:
    ansible_connection: arubanetworks.aoscx.aoscx
    ansible_network_os: arubanetworks.aoscx.aoscx
    ansible_become: false
    
    # Configuration de la mise à jour firmware
    firmware_file_path: "/opt/firmware/ArubaOS-CX_6200_10_10_1040.swi"
    target_firmware_version: "LL.10.10.1040"
    
    # Configuration du serveur de dépôt
    repository_server: "backup.example.com"
    repository_path: "/backups/network/aruba"
    
    # Options de mise à jour
    partition_strategy: "auto"
    backup_config: true
    rollback_on_failure: true
    
  roles:
    - firmware_updater
```

### Exécution

```bash
# Mise à jour complète
ansible-playbook -i inventory/switches.yml update_firmware.yml --ask-pass

# Vérification uniquement (sans mise à jour)
ansible-playbook -i inventory/switches.yml update_firmware.yml --tags check

# Upload seulement (sans redémarrage)
ansible-playbook -i inventory/switches.yml update_firmware.yml --tags check,upload

# Avec fichier vault pour les mots de passe
ansible-playbook -i inventory/switches.yml update_firmware.yml --vault-password-file=.vault_pass
```

## Étiquettes (Tags)

| Tag | Description |
|-----|-------------|
| `check` | Vérifications préalables et collecte d'état |
| `backup` | Sauvegarde de la configuration |
| `upload` | Upload du firmware |
| `reboot` | Redémarrage du switch |
| `verify` | Vérifications post-update |
| `cleanup` | Nettoyage des fichiers temporaires |
| `always` | Toutes les étapes (par défaut) |
| `never` | Étapes de debug uniquement |

## Stratégies de partition

### Stratégie automatique (`auto`)
- Si la version cible est déjà sur une partition → utilise cette partition
- Sinon → utilise la partition alternative pour préserver le rollback
- Choix intelligent pour minimiser les risques

### Stratégies manuelles
- `primary` : Force l'utilisation de la partition primary
- `secondary` : Force l'utilisation de la partition secondary

## Gestion des erreurs et rollback

### Types d'erreurs gérées
1. **Erreurs de prérequis** : espace disque, connectivité, permissions
2. **Erreurs d'upload** : timeout, corruption, espace insuffisant
3. **Erreurs de redémarrage** : switch inaccessible, timeout
4. **Erreurs de vérification** : version incorrecte, dysfonctionnement

### Mécanisme de rollback
- **Automatique** : si `rollback_on_failure: true`
- **Conditions** : échec de vérification avec partition de rollback disponible
- **Processus** : redémarrage sur l'ancienne partition + vérification

## Timeouts adaptatifs par modèle

Le rôle ajuste automatiquement les timeouts selon le modèle de switch :

| Modèle | Upload (min) | Reboot (min) |
|--------|--------------|--------------|
| 6100   | 40           | 8            |
| 6200   | 30           | 10           |
| 6300   | 35           | 12           |
| 6400   | 40           | 15           |
| 8320   | 50           | 20           |
| 8400   | 60           | 25           |

## Rapports et logging

### Rapport de mise à jour
- **Format** : Markdown ou JSON
- **Contenu** : état avant/après, durées, erreurs, vérifications
- **Stockage** : serveur de dépôt externe

### Logs détaillés
- Chaque étape est loggée avec timestamps
- Erreurs capturées avec contexte
- Métriques de performance enregistrées

## Compatibilité

### Switches supportés
- Aruba CX 6100 series
- Aruba CX 6200 series  
- Aruba CX 6300 series
- Aruba CX 6400 series
- Aruba CX 8320 series
- Aruba CX 8325 series
- Aruba CX 8400 series

### Versions AOS-CX
- Minimum : 10.04
- Recommandé : 10.08+
- Testé jusqu'à : 10.13

## Sécurité

### Prérequis sécuritaires
- API REST configurée en mode read-write
- Utilisateur avec privilèges administrateur
- Connexion sécurisée (HTTPS)
- Serveur de dépôt avec accès SSH

### Bonnes pratiques
- Utiliser Ansible Vault pour les mots de passe
- Tester sur environnement de lab avant production
- Planifier les fenêtres de maintenance
- Vérifier la compatibilité firmware/matériel

## Limitations connues

1. **VSX** : Les clusters VSX nécessitent une procédure spécifique
2. **Stack** : Les stacks de switches ne sont pas supportés
3. **Downgrade** : Le downgrade de firmware n'est pas recommandé
4. **Espace disque** : Vérification basée sur l'espace primary uniquement

## Dépannage

### Problèmes courants

#### Upload échoue avec erreur 401/403
```bash
# Vérifier la configuration API REST
show https-server

# Activer si nécessaire
https-server rest access-mode read-write
```

#### Switch inaccessible après reboot
1. Vérifier les LEDs du switch
2. Accès console série requis
3. Vérifier la configuration réseau
4. Possible rollback manuel nécessaire

#### Timeout durant l'upload
- Vérifier la bande passante réseau
- Augmenter `max_upload_time`
- Utiliser `upload_method: remote` si possible

### Debug avancé

```bash
# Mode verbose complet
ansible-playbook update_firmware.yml -vvv

# Debug spécifique
ansible-playbook update_firmware.yml --tags debug,never

# Test de connectivité uniquement
ansible-playbook update_firmware.yml --tags check --check
```

## Auteur

Créé pour le projet Aruba Manager - Automatisation des infrastructures réseau Aruba.