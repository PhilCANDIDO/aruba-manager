# Configuration du Vault pour le rôle simple_firmware_updater

## Variables requises dans le vault

Le rôle `simple_firmware_updater` utilise automatiquement les variables suivantes depuis votre vault pour les opérations sur le serveur repository :

```yaml
# Serveur de dépôt
repository_server: 10.20.3.11        # Adresse IP ou nom d'hôte du serveur
repository_user: deploy              # Utilisateur pour la connexion SSH
repository_password: VotreMotDePasse # Mot de passe SSH
repository_become_password: VotreMotDePasseSudo  # Mot de passe pour sudo/become
```

## Création ou édition du vault

### Créer un nouveau vault
```bash
ansible-vault create group_vars/all/vault.yml
```

### Éditer un vault existant
```bash
ansible-vault edit group_vars/all/vault.yml
```

### Voir le contenu du vault
```bash
ansible-vault view group_vars/all/vault.yml
```

## Exemple de fichier vault complet

```yaml
# Credentials pour les switches Aruba
aruba_user: admin
aruba_password: MonMotDePasseAruba

# Credentials pour le serveur de dépôt
repository_server: 10.20.3.11
repository_user: deploy
repository_password: Passw0rd
repository_become_password: Passw0rd

# Autres variables sensibles...
```

## Utilisation

Une fois le vault configuré, vous n'avez plus besoin d'utiliser `--ask-become-pass` :

```bash
# Backup uniquement
ansible-playbook -i inventory/switches.yml simple_firmware_update.yml \
  -e "switch_model=6000" \
  -e "firmware_filename=ArubaOS-CX_6100-6000_10_13_1120.swi" \
  --tags "backup" \
  --ask-vault-pass
```

Le rôle utilisera automatiquement les credentials du vault pour :
- Se connecter au serveur repository
- Élever les privilèges avec sudo
- Créer les répertoires nécessaires
- Transférer les fichiers de sauvegarde

## Sécurité

- Ne jamais commiter le fichier vault non chiffré
- Ajouter `*.vault` et `vault.yml` à votre `.gitignore`
- Utiliser un mot de passe fort pour le vault
- Limiter l'accès au mot de passe du vault aux personnes autorisées