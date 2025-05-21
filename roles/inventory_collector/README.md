# Rôle Ansible: inventory_collector

Ce rôle permet de collecter des informations d'inventaire des commutateurs Aruba AOS-CX et de les exporter dans un fichier Excel qui sera transféré vers un serveur de dépôt externe pour stockage permanent.

## Prérequis

- Ansible 2.10 ou supérieur
- Collection Ansible Aruba AOS-CX : `arubanetworks.aoscx`
- Modules Python requis sur le contrôleur Ansible :
  - `openpyxl`
  - `pandas`
- Serveur de dépôt externe configuré (SFTP, FTP ou SMB)

## Informations collectées

Ce rôle collecte automatiquement les informations suivantes pour chaque équipement :

- Nom du switch
- Modèle (référence matérielle)
- Numéro de série
- Version du système d'exploitation
- Adresse IP (issue de l'inventaire)
- Date et heure de la collecte

## Variables

### Variables obligatoires

| Variable | Description |
|----------|-------------|
| `repository_server` | Serveur de dépôt pour stockage permanent des rapports |
| `repository_path` | Chemin sur le serveur de dépôt |

### Variables par défaut (defaults/main.yml)

| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| `repository_protocol` | Protocole de transfert | `"sftp"` |
| `repository_user` | Utilisateur pour la connexion au serveur | `""` |
| `repository_port` | Port pour la connexion | `22` |
| `repository_password` | Mot de passe (à définir via Ansible Vault) | - |
| `temp_inventory_path` | Chemin temporaire pour les fichiers | Généré automatiquement |
| `report_filename` | Nom du fichier sur le serveur de dépôt | `"inventaire_aruba_DATE_HEURE.xlsx"` |
| `max_tentatives` | Nombre maximal de tentatives de connexion | `3` |
| `delai_attente` | Délai d'attente pour les opérations (secondes) | `60` |
| `cleanup_temp_files` | Nettoyer les fichiers temporaires | `true` |

## Utilisation

### Exemple de playbook

```yaml
---
- name: Collect Aruba switches inventory
  hosts: switches_aruba
  gather_facts: false
  vars:
    ansible_connection: network_cli
    ansible_network_os: arubanetworks.aoscx.aoscx
    ansible_become: false
    ansible_user: admin
    
    # Configuration du serveur de dépôt
    repository_server: "repository.example.com"
    repository_user: "backup"
    repository_path: "/backups/network/aruba"
    repository_protocol: "sftp"
    
  roles:
    - inventory_collector
```

### Exécution

```bash
ansible-playbook -i inventory/switches.yml collect_inventory.yml --ask-pass
```

Avec un fichier vault pour les mots de passe :

```bash
ansible-playbook -i inventory/switches.yml collect_inventory.yml --vault-password-file=.vault_pass
```

## Étiquettes (Tags)

Le rôle utilise les étiquettes suivantes :

- `check` : Vérification des prérequis
- `collect` : Collecte des informations sur les équipements
- `validate` : Validation des données collectées
- `export` : Exportation des données vers Excel
- `transfer` : Transfert vers le serveur de dépôt
- `cleanup` : Nettoyage des fichiers temporaires
- `always` : Appliqué à toutes les tâches (exécution complète)

## Flux de travail

1. Vérification des prérequis (modules Python, collection Ansible)
2. Collecte des informations pour chaque switch
3. Validation et consolidation des données
4. Exportation vers un fichier Excel temporaire
5. Transfert du fichier vers le serveur de dépôt externe
6. Nettoyage des fichiers temporaires sur le nœud contrôleur

## Gestion des erreurs

Le rôle est conçu pour être robuste face aux erreurs de connexion. Si un équipement est inaccessible, il sera marqué comme "ÉCHEC DE COLLECTE" dans le rapport final, mais le processus continuera pour les autres équipements.

## Non-persistance des données

Conformément aux exigences pour l'environnement AWX, ce rôle ne conserve aucune donnée sur le nœud contrôleur :
- Tous les fichiers sont créés dans un répertoire temporaire
- Le rapport est transféré vers un serveur de dépôt externe
- Les fichiers temporaires sont supprimés après transfert

## Idempotence

Ce rôle est idempotent et peut être exécuté plusieurs fois sans effets secondaires. Chaque exécution générera un nouveau fichier d'inventaire avec la date et l'heure d'exécution.

## Compatibilité AWX/Ansible Tower

Ce rôle a été conçu spécifiquement pour fonctionner dans un environnement AWX sans stockage persistant. L'utilisation d'un serveur de dépôt externe garantit que les rapports sont conservés même après la suppression du nœud contrôleur.

## Limitations connues

- Fonctionne uniquement avec les commutateurs Aruba AOS-CX. Pour d'autres modèles, des adaptations seront nécessaires.
- Le transfert vers le serveur de dépôt requiert une configuration réseau appropriée entre le nœud contrôleur et le serveur.

## Auteur

Créé par [Votre Nom] pour le projet Aruba Manager.