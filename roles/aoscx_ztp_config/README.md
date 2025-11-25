# Ansible Role: aoscx_ztp_config

Zero Touch Provisioning (ZTP) configuration role for Aruba AOS-CX switches. This role automates the complete initialization and configuration of factory-reset Aruba switches.

## Description

This role provides a complete ZTP workflow for Aruba AOS-CX switches, from initial password setup through full network configuration. It's designed to take a factory-reset switch and configure it with all necessary settings for production deployment.

## Features

- **Initial Authentication**: Automatically sets password on factory-reset switches
- **DNS/NTP Configuration**: Configures time synchronization and name resolution
- **VLAN Management**: Creates and configures multiple VLANs
- **Aruba Central**: Disables Aruba Central cloud management
- **Spanning Tree**: Configures RPVST with BPDU guard and loop protection
- **AAA Authentication**: Sets up RADIUS and TACACS+ for 802.1X and management access
- **Trunk Interfaces**: Configures uplink/interconnect ports
- **SNMP**: Sets up SNMPv3 monitoring
- **Management Network**: Configures management VLAN IP and default route

## Requirements

### Ansible Version
- Ansible >= 2.9

### Collections
```bash
ansible-galaxy collection install arubanetworks.aoscx
```

### Python Libraries
```bash
pip3 install paramiko
```

### Switch Requirements
- Aruba AOS-CX switch (any model)
- Switch must be reachable via network
- For initial setup: factory-reset state (blank password)

## Role Variables

### Required Variables (must be defined in inventory or vault)

#### Authentication & Credentials
```yaml
aruba_user: admin                    # Switch username
aruba_password: "SecurePassword"     # Switch password (vault recommended)
radius_key: "RadiusSecret"           # RADIUS/TACACS shared secret (vault recommended)
```

#### VLAN Configuration
```yaml
pc_vlan: 3000        # PC/workstation VLAN
pc_admin: 3100       # Admin PC VLAN
toip: 3200           # VoIP VLAN
impr: 3300           # Printer VLAN
priv: 3400           # Private VLAN
secu: 3500           # Security VLAN
gtc: 3600            # GTC VLAN
rso: 100             # RSO admin VLAN (used for management IP)
adm_wifi: 101        # WiFi admin VLAN
wifi_perm: 500       # WiFi data VLAN
```

#### RADIUS/TACACS Servers
```yaml
rad1: 10.20.5.1      # Primary AAA server
rad2: 10.20.5.2      # Secondary AAA server
rad3: 10.20.5.3      # Tertiary AAA server
```

#### SNMP Configuration
```yaml
snmp_key: "SNMPAuthPass"       # SNMPv3 auth password (vault recommended)
snmp_encrypt: "SNMPPrivPass"   # SNMPv3 priv password (vault recommended)
```

#### Management Network
```yaml
target_ip: 10.100.144.1        # Management IP for the switch (VLAN {{ rso }})
site_gateway: 10.100.11.253    # Default gateway
```

### Optional Variables

All variables can be overridden in inventory, group_vars, or playbook vars.

## Dependencies

None.

## Task Files

The role is organized into modular task files for easy maintenance and selective execution:

| File | Description | Tags |
|------|-------------|------|
| `00_ztp_init_connection.yml` | Initial password setup on factory switch | `ztp_init`, `ztp_auth`, `initial_password` |
| `01_dns_ntp.yml` | DNS and NTP configuration | `dns`, `ntp`, `dns_ntp` |
| `02_vlans.yml` | VLAN creation and voice attribute | `vlans` |
| `03_aruba_central_stp.yml` | Disable Aruba Central, configure STP | `aruba_central`, `stp`, `spanning_tree` |
| `04_radius_tacacs.yml` | RADIUS/TACACS+ and 802.1X setup | `radius`, `tacacs`, `aaa`, `authentication` |
| `05_trunk_interfaces.yml` | Configure uplink/trunk ports (1/1/48-50) | `trunk`, `interfaces`, `rocades` |
| `06_snmp_mgmt.yml` | SNMP, management IP, and routing | `snmp`, `management`, `mgmt`, `routing` |

## Example Inventory

### INI Format (`inventory/switches_test.ini`)

```ini
[switches_aruba_test]
switch01 ansible_host=10.13.0.36

[switches_aruba_test:vars]
ansible_connection=arubanetworks.aoscx.aoscx
ansible_network_os=arubanetworks.aoscx.aoscx
ansible_httpapi_validate_certs=false
ansible_httpapi_use_ssl=true
ansible_acx_no_proxy=true
ansible_become=false
ansible_user="{{ aruba_user }}"
ansible_password="{{ aruba_password }}"
radius_key="{{ radius_key }}"
snmp_key="{{ snmp_key }}"
snmp_encrypt="{{ snmp_encrypt }}"

# VLAN IDs
pc_vlan=3000
pc_admin=3100
toip=3200
impr=3300
priv=3400
secu=3500
gtc=3600
rso=100
adm_wifi=101
wifi_perm=500

# Network Configuration
site_gateway=10.100.11.253
target_ip=10.100.144.1

# AAA Servers
rad1=10.20.5.1
rad2=10.20.5.2
rad3=10.20.5.3
```

### YAML Format

```yaml
all:
  children:
    switches_aruba_test:
      hosts:
        switch01:
          ansible_host: 10.13.0.36
      vars:
        ansible_connection: arubanetworks.aoscx.aoscx
        ansible_network_os: arubanetworks.aoscx.aoscx
        ansible_httpapi_validate_certs: false
        ansible_httpapi_use_ssl: true
        ansible_become: false
        ansible_user: "{{ aruba_user }}"
        ansible_password: "{{ aruba_password }}"
        # ... other vars ...
```

## Example Playbook

### Basic Usage

```yaml
---
- name: Zero Touch Provisioning - Initialize Factory Switch
  hosts: switches_aruba_test
  gather_facts: no

  roles:
    - aoscx_ztp_config
```

### With Variable Overrides

```yaml
---
- name: ZTP with custom VLANs
  hosts: switches_aruba_test
  gather_facts: no

  vars:
    pc_vlan: 100
    toip: 200

  roles:
    - aoscx_ztp_config
```

### Running Specific Tasks with Tags

```yaml
---
- name: Configure only VLANs and RADIUS
  hosts: switches_aruba_test
  gather_facts: no

  roles:
    - role: aoscx_ztp_config
      tags:
        - vlans
        - radius
```

## Usage Examples

### Complete ZTP Process (Factory Switch)

```bash
# Run complete ZTP including initial password setup
ansible-playbook -i inventory/switches_test.ini ztp_init_factory_switch.yml --ask-vault-pass
```

### Skip Initial Password Setup (Already Configured)

```bash
# Skip ZTP auth if switch already has password
ansible-playbook -i inventory/switches_test.ini ztp_init_factory_switch.yml --skip-tags ztp_init --ask-vault-pass
```

### Run Only Specific Configuration Sections

```bash
# Configure only VLANs
ansible-playbook -i inventory/switches_test.ini ztp_init_factory_switch.yml --tags vlans --ask-vault-pass

# Configure only DNS/NTP
ansible-playbook -i inventory/switches_test.ini ztp_init_factory_switch.yml --tags dns_ntp --ask-vault-pass

# Configure only RADIUS/TACACS
ansible-playbook -i inventory/switches_test.ini ztp_init_factory_switch.yml --tags aaa --ask-vault-pass

# Configure only trunk interfaces
ansible-playbook -i inventory/switches_test.ini ztp_init_factory_switch.yml --tags trunk --ask-vault-pass
```

### Reconfigure Management Network

```bash
# Update management IP and routing
ansible-playbook -i inventory/switches_test.ini ztp_init_factory_switch.yml --tags management --ask-vault-pass
```

### Dry Run (Check Mode)

```bash
# Note: Check mode won't work for initial ZTP auth due to SSH interaction requirement
ansible-playbook -i inventory/switches_test.ini ztp_init_factory_switch.yml --check --ask-vault-pass
```

## Task Identification

Each task name includes the source file in parentheses for easy identification during playbook execution:

```
TASK [(ztp_init_connection) Configure initial password on factory switch]
TASK [(dns_ntp) Configure DNS servers]
TASK [(vlans) Add PC VLAN]
TASK [(radius_tacacs) Configure RADIUS servers]
TASK [(trunk_interfaces) Configure Interface 1/1/48 as trunk]
TASK [(snmp_mgmt) Configure SNMP]
```

This makes it easy to identify which task file contains a specific task when reviewing logs or troubleshooting.

## Security Recommendations

### Use Ansible Vault

Store sensitive variables in an encrypted vault file:

```bash
# Create a vault file
ansible-vault create group_vars/switches_aruba_test/vault.yml
```

```yaml
# Contents of vault.yml
aruba_user: admin
aruba_password: "YourSecurePassword123!"
radius_key: "RadiusSharedSecret"
snmp_key: "SNMPAuthPassword"
snmp_encrypt: "SNMPPrivPassword"
```

### Encrypt Individual Variables

```bash
ansible-vault encrypt_string 'MyPassword123' --name 'aruba_password'
```

Then paste the output into your inventory or vars file.

## Network Requirements

### Prerequisites

- **Port 51 or 52**: Must have BASE-T GBIC installed before script execution
- **Management Access**: Ansible control node must reach switch management IP
- **HTTPS API**: Switch must have HTTPS enabled (default on AOS-CX)

### Firewall Rules

Ensure the following ports are accessible:
- **TCP 443**: HTTPS API (aoscx connection plugin)
- **TCP 22**: SSH (for initial ZTP auth only)

## Switch Configuration Applied

### Interfaces Modified

- **1/1/1 - 1/1/47**: Access ports with RADIUS/TACACS authentication
- **1/1/48 - 1/1/50**: Trunk ports (Rocades/Uplinks) with all VLANs allowed

### Network Services

- **DNS**: 10.20.1.2, 10.20.1.3 (domain: cg05.lan)
- **NTP**: ntp.cg05.lan
- **Timezone**: Europe/Paris
- **CDP**: Disabled
- **Spanning Tree**: RPVST with BPDU guard and loop protection
- **Aruba Central**: Disabled

### Authentication

- **TACACS+**: Management access authentication
- **RADIUS**: 802.1X and MAC authentication for port access
- **Local Fallback**: Enabled for management access

## Troubleshooting

### Common Issues

#### 1. "couldn't resolve module/action 'aoscx_ztp_auth'"

**Cause**: Custom module not found

**Solution**: Ensure `ansible.cfg` has module paths configured:
```ini
[defaults]
library = ./plugins/modules
module_utils = ./plugins/module_utils
```

#### 2. Initial ZTP authentication fails

**Cause**: Switch not in factory-reset state

**Solution**:
- Verify switch has blank password
- Skip ZTP auth step: `--skip-tags ztp_init`

#### 3. RADIUS/TACACS configuration fails

**Cause**: Missing vault variables

**Solution**: Ensure `radius_key` is defined in vault

#### 4. Connection timeout

**Cause**: Network connectivity or firewall

**Solution**:
- Verify switch IP is reachable: `ping <switch_ip>`
- Check HTTPS is accessible: `curl -k https://<switch_ip>`

## License

GPL-3.0-or-later

## Author Information

Conseil Départemental des Hautes-Alpes

## Version History

- **1.0.0** (2025-11-25): Initial release
  - Complete ZTP workflow
  - Modular task files
  - Tag-based execution
  - Vault integration
