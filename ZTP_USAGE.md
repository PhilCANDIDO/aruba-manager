# Zero Touch Provisioning (ZTP) Usage Guide

This guide explains how to use the ZTP authentication module to configure Aruba AOSCX switches from factory settings.

## Overview

Zero Touch Provisioning allows you to automatically configure switches that are in factory-reset state (with blank passwords). The process has two main steps:

1. **Initial Authentication** - Set up the admin password (using `aoscx_ztp_auth` module)
2. **Full Configuration** - Apply complete configuration (using `ZTP_0toHero.yml`)

## Prerequisites

### 1. Switch Requirements
- Switch must be in **factory-reset state** (blank password)
- Switch must be **reachable on the network**
- SSH must be enabled (enabled by default on factory-reset switches)

### 2. Software Requirements
```bash
# Install Python dependencies
pip3 install paramiko

# Install Aruba AOSCX Ansible collection
ansible-galaxy collection install arubanetworks.aoscx
```

### 3. Network Setup
- Ensure the Ansible control node can reach the switch IP
- Default factory credentials: `username=admin`, `password=(blank)`

## Files Created

```
plugins/
├── modules/
│   └── aoscx_ztp_auth.py          # Ansible module for ZTP authentication
└── module_utils/
    └── aoscx_ztp.py                # Utility functions (from Aruba)

Playbooks:
├── ztp_auth_simple.yml             # Simple single-switch test
├── ztp_bulk_auth.yml               # Multiple switches authentication
├── test_ztp_auth.yml               # Interactive test with prompts
└── ZTP_0toHero.yml                 # Full configuration (existing)

Inventory:
└── inventory/
    └── factory_switches.yml        # Inventory for factory switches
```

## Usage Examples

### Method 1: Simple Test (Single Switch)

Edit the variables in `ztp_auth_simple.yml`:

```yaml
vars:
  switch_ip: "192.168.1.100"
  new_password: "YourSecureP@ss!"
```

Run:
```bash
ansible-playbook ztp_auth_simple.yml
```

### Method 2: Interactive Test

This will prompt you for the IP and password:

```bash
ansible-playbook test_ztp_auth.yml
```

### Method 3: Bulk Authentication (Multiple Switches)

1. Edit `inventory/factory_switches.yml`:
```yaml
factory_switches:
  hosts:
    switch01:
      ansible_host: 192.168.1.100
      ztp_password: "Pass1!"
    switch02:
      ansible_host: 192.168.1.101
      ztp_password: "Pass2!"
```

2. Run the bulk playbook:
```bash
ansible-playbook -i inventory/factory_switches.yml ztp_bulk_auth.yml
```

### Method 4: Complete ZTP Workflow

After authentication, run the full configuration:

```bash
# Step 1: Authenticate
ansible-playbook -i inventory/factory_switches.yml ztp_bulk_auth.yml

# Step 2: Full configuration
ansible-playbook -i inventory/switches.yml ZTP_0toHero.yml
```

## Module Documentation

### aoscx_ztp_auth

Configures authentication on factory-reset switches.

**Parameters:**
- `hostname` (required) - IP address or hostname of the switch
- `username` (optional) - Username to configure (default: `admin`)
- `password` (required) - New password to set

**Example:**
```yaml
- name: Setup authentication
  aoscx_ztp_auth:
    hostname: 192.168.1.100
    username: admin
    password: "MySecureP@ss!"
```

## Troubleshooting

### Error: "Unable to authenticate"

**Cause:** Switch is not in factory-reset state (password already configured)

**Solutions:**
1. Verify the switch is truly factory-reset
2. Try connecting manually: `ssh admin@<switch_ip>` (should not ask for password)
3. Factory-reset the switch if needed

### Error: "Connection timeout"

**Causes:**
- Network connectivity issues
- Wrong IP address
- Firewall blocking SSH

**Solutions:**
1. Test connectivity: `ping <switch_ip>`
2. Test SSH: `telnet <switch_ip> 22`
3. Check firewall rules

### Error: "paramiko not found"

**Solution:**
```bash
pip3 install paramiko
```

### Error: "Could not import aoscx_ztp module"

**Cause:** Module path issue

**Solution:**
Verify file exists:
```bash
ls -la plugins/module_utils/aoscx_ztp.py
```

## Security Best Practices

### 1. Use Ansible Vault for Passwords

Encrypt passwords in inventory:
```bash
ansible-vault encrypt_string 'YourPassword' --name 'ztp_password'
```

Add to inventory:
```yaml
factory_switches:
  hosts:
    switch01:
      ansible_host: 192.168.1.100
      ztp_password: !vault |
        $ANSIBLE_VAULT;1.1;AES256
        ...encrypted content...
```

### 2. Store Credentials Externally

Use environment variables or external credential managers:
```bash
export ZTP_PASSWORD="YourPassword"
ansible-playbook ztp_bulk_auth.yml -e "ztp_password=$ZTP_PASSWORD"
```

### 3. Use Strong Passwords

Ensure passwords meet security requirements:
- Minimum 8 characters
- Mix of upper/lowercase, numbers, special characters
- Avoid common passwords

## What Happens During ZTP Authentication

1. Module connects to switch via SSH using default credentials (`admin` / blank password)
2. Switch prompts: `Enter new password:`
3. Module sends the new password
4. Switch prompts: `Confirm new password:`
5. Module confirms the password
6. Switch accepts the configuration and shows CLI prompt `#`
7. Module reports success

## Next Steps After Authentication

Once authentication is configured, proceed with full switch configuration:

1. Update your main inventory with the new credentials
2. Run the full configuration playbook: `ZTP_0toHero.yml`
3. The full configuration includes:
   - DNS/NTP setup
   - VLAN creation
   - RADIUS/TACACS configuration
   - Spanning tree setup
   - Interface configuration
   - SNMP setup

## Testing the Module Manually

To test the module behavior:

```bash
# Run with verbose output
ansible-playbook ztp_auth_simple.yml -vvv

# Check mode (dry-run) - NOT SUPPORTED for this module
# This module cannot run in check mode as it requires actual SSH interaction
```

## Integration with Existing Workflow

Your existing `ZTP_0toHero.yml` playbook should be run AFTER authentication:

```bash
# Complete ZTP workflow
ansible-playbook ztp_bulk_auth.yml && \
ansible-playbook ZTP_0toHero.yml
```

Or create a master playbook that calls both:

```yaml
---
- import_playbook: ztp_bulk_auth.yml
- import_playbook: ZTP_0toHero.yml
```

## Support

For issues or questions:
- Check Aruba AOSCX Ansible collection docs
- Review paramiko library documentation
- Verify switch is in proper factory-reset state
