# Guide de Mise à Jour Firmware Aruba AOS-CX

## Installation et Configuration

### 1. Prérequis système

```bash
# Installer les dépendances Python
pip3 install pyaoscx>=2.6.0 jmespath openpyxl pandas

# Installer les collections Ansible
ansible-galaxy collection install arubanetworks.aoscx
ansible-galaxy collection install ansible.netcommon
```

### 2. Configuration des switches

Sur chaque switch Aruba AOS-CX :

```bash
# Activer l'API REST
switch(config)# https-server rest access-mode read-write
switch(config)# https-server vrf mgmt

# Vérifier la configuration
switch# show https-server
```

### 3. Configuration du serveur de dépôt

```bash
# Créer les répertoires sur le serveur de dépôt
sudo mkdir -p /backups/network/aruba/{config_backups,firmware_updates}
sudo chown ansible:ansible /backups/network/aruba
```

## Utilisation Rapide

### Mise à jour simple

```bash
# 1. Copier le fichier firmware
cp ArubaOS-CX_6200_10_10_1040.swi /opt/firmware/

# 2. Éditer le playbook avec vos paramètres
vim mise_a_jour_firmware.yml

# 3. Exécuter la mise à jour
ansible-playbook -i inventory/switches.yml mise_a_jour_firmware.yml --ask-pass
```

### Variables principales à configurer

```yaml
# Dans mise_a_jour_firmware.yml
vars:
  firmware_file_path: "/opt/firmware/votre_firmware.swi"
  target_firmware_version: "LL.XX.YY.ZZZZ"
  repository_server: "votre-serveur-backup.com"
  repository_path: "/backups/network/aruba"
```

## Scénarios d'Utilisation

### 1. Vérification uniquement (dry-run)

```bash
# Vérifier l'état sans faire de changements
ansible-playbook mise_a_jour_firmware.yml --tags check --check
```

### 2. Upload sans redémarrage

```bash
# Upload le firmware sans redémarrer
ansible-playbook mise_a_jour_firmware.yml --tags check,upload
```

### 3. Mise à jour forcée

```yaml
# Dans le playbook, ajouter :
force_update: true
```

### 4. Mise à jour d'urgence (timeouts réduits)

```yaml
# Réduire les timeouts pour maintenance urgente
max_upload_time: 900    # 15 minutes
max_reboot_time: 300    # 5 minutes
```

## Validation du Firmware

### Avant la mise à jour

```bash
# Valider le fichier firmware
python3 roles/firmware_updater/files/firmware_validator.py \
  --model 6200 \
  /opt/firmware/ArubaOS-CX_6200_10_10_1040.swi
```

### Checksum de sécurité

```bash
# Générer le checksum pour vérification
python3 roles/firmware_updater/files/firmware_validator.py \
  --checksum-only \
  /opt/firmware/ArubaOS-CX_6200_10_10_1040.swi
```

## Gestion par Modèle de Switch

### Configuration spécifique par modèle

```yaml
# Dans group_vars/ ou host_vars/
# Pour switches 6100 (plus lents)
max_upload_time: 2400   # 40 minutes
max_reboot_time: 480    # 8 minutes

# Pour switches 8400 (plus gros)
max_upload_time: 3600   # 60 minutes  
max_reboot_time: 1500   # 25 minutes
```

## Dépannage Rapide

### Problèmes fréquents

#### 1. Erreur 401/403 lors de l'upload

```bash
# Sur le switch, vérifier :
show https-server
# Si nécessaire :
https-server rest access-mode read-write
```

#### 2. Switch inaccessible après reboot

```bash
# Vérifier les LEDs physiques
# Accès console série si disponible
# Le rôle inclut une récupération d'urgence automatique
```

#### 3. Espace disque insuffisant

```bash
# Sur le switch, libérer de l'espace :
show image
boot system secondary delete  # Supprimer l'ancienne image
```

#### 4. Timeout durant l'upload

```yaml
# Augmenter les timeouts dans le playbook :
max_upload_time: 3600  # 1 heure
```

### Commandes de diagnostic

```bash
# Vérifier l'état des switches
ansible switches_aruba -m arubanetworks.aoscx.aoscx_facts \
  -a "gather_subset=['software_version','software_images']"

# Tester la connectivité
ansible switches_aruba -m arubanetworks.aoscx.aoscx_command \
  -a "commands=['show version']"
```

## Sécurité et Bonnes Pratiques

### 1. Mots de passe sécurisés

```bash
# Utiliser Ansible Vault
ansible-vault create group_vars/switches_aruba/vault.yml

# Dans le vault :
vault_ansible_password: "votre_mot_de_passe_securise"

# Dans l'inventaire :
ansible_password: "{{ vault_ansible_password }}"
```

### 2. Planification de maintenance

```yaml
# Ajouter une pause de confirmation
- name: Confirmation avant mise à jour
  pause:
    prompt: "Confirmer la mise à jour en production (yes/no)"
  when: not force_update | bool
```

### 3. Sauvegarde avant intervention

```bash
# S'assurer que les sauvegardes sont activées
backup_config: true
backup_method: "local"
keep_backup_count: 5
```

## Monitoring et Rapports

### Accès aux rapports

```bash
# Sur le serveur de dépôt
ls -la /backups/network/aruba/firmware_updates/
cat /backups/network/aruba/firmware_updates/switch_YYYYMMDD_HHMMSS_report.md
```

### Logs détaillés

```bash
# Exécution avec logs verbeux
ansible-playbook mise_a_jour_firmware.yml -vvv > update.log 2>&1
```

### Statut post-mise à jour

```bash
# Vérifier le succès
ansible switches_aruba -m arubanetworks.aoscx.aoscx_command \
  -a "commands=['show version','show image']" | grep -E "(Version|Image)"
```

## Support et Ressources

### Documentation officielle
- [Aruba AOS-CX Ansible Collection](https://galaxy.ansible.com/arubanetworks/aoscx)
- [Documentation AOS-CX](https://developer.arubanetworks.com/)

### Logs et débogage
- Logs Ansible : `/var/log/ansible.log`
- Rapports : `{{ repository_path }}/firmware_updates/`
- Sauvegardes : `{{ repository_path }}/config_backups/`

### Contact support
En cas de problème critique, contacter l'équipe réseau avec :
- Le rapport de mise à jour généré
- Les logs Ansible complets
- L'état actuel du switch (version, accessibilité)