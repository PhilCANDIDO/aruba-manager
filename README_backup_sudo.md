# Configuration sudo pour les sauvegardes

## Problème

Lors de l'exécution du playbook avec uniquement le tag `backup`, Ansible a besoin du mot de passe sudo pour créer les répertoires sur le serveur repository.

## Solutions

### Option 1 : Utiliser --ask-become-pass

```bash
ansible-playbook -i inventory/switches.yml simple_firmware_update.yml \
  -e "switch_model=6000" \
  -e "firmware_filename=ArubaOS-CX_6100-6000_10_13_1120.swi" \
  --tags "backup" \
  --ask-vault-pass \
  --ask-become-pass
```

### Option 2 : Configurer ansible.cfg

Ajoutez dans votre fichier `ansible.cfg` :

```ini
[privilege_escalation]
become = True
become_method = sudo
become_user = root
become_ask_pass = True
```

### Option 3 : Utiliser un vault pour le mot de passe sudo

1. Créez un fichier vault avec le mot de passe sudo :
```bash
ansible-vault create group_vars/all/sudo_pass.yml
```

2. Ajoutez dans ce fichier :
```yaml
ansible_become_pass: votre_mot_de_passe_sudo
```

3. Exécutez le playbook :
```bash
ansible-playbook -i inventory/switches.yml simple_firmware_update.yml \
  -e "switch_model=6000" \
  -e "firmware_filename=ArubaOS-CX_6100-6000_10_13_1120.swi" \
  --tags "backup" \
  --ask-vault-pass
```

### Option 4 : Configurer sudo sans mot de passe (non recommandé en production)

Sur le serveur repository, configurez sudo pour l'utilisateur ansible :
```bash
echo "ansible ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/ansible
```

## Recommandation

Pour les environnements de production, utilisez l'option 3 (vault) qui est la plus sécurisée.