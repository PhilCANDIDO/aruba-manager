#!/usr/bin/python
# -*- coding: utf-8 -*-

# (C) Copyright 2020-2025 Hewlett Packard Enterprise Development LP.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: aoscx_ztp_auth
version_added: "1.0.0"
short_description: Configure authentication on factory-reset Aruba AOSCX switches
description:
  - This module connects to a factory-reset (zeroized) Aruba AOSCX switch via SSH
  - It uses the default credentials (username 'admin', blank password)
  - Sets up a new password for the switch
  - This is typically the first step in Zero Touch Provisioning (ZTP)
author:
  - Aruba Networks
options:
  hostname:
    description:
      - The IP address or hostname of the target switch
    required: true
    type: str
  username:
    description:
      - The username to configure on the switch
      - Default is 'admin' for factory-reset switches
    required: false
    type: str
    default: admin
  password:
    description:
      - The new password to set for the switch
      - This will be used for all subsequent connections
    required: true
    type: str
    no_log: true
notes:
  - This module requires the paramiko Python library
  - The switch must be in factory-reset state (blank password)
  - If the switch already has a password configured, the module will log an error
requirements:
  - paramiko
"""

EXAMPLES = r"""
# Configure authentication on a factory-reset switch
- name: Setup ZTP authentication
  aoscx_ztp_auth:
    hostname: 192.168.1.100
    username: admin
    password: "MySecureP@ssw0rd!"

# Configure authentication with custom username
- name: Setup ZTP authentication with custom user
  aoscx_ztp_auth:
    hostname: 10.20.1.50
    username: netadmin
    password: "{{ switch_password }}"

# Use in a playbook with inventory
- name: Configure multiple switches from factory reset
  hosts: factory_switches
  gather_facts: no
  tasks:
    - name: Initialize switch authentication
      aoscx_ztp_auth:
        hostname: "{{ ansible_host }}"
        username: "{{ ztp_username | default('admin') }}"
        password: "{{ ztp_password }}"
"""

RETURN = r"""
msg:
  description: Result message indicating success or failure
  returned: always
  type: str
  sample: "Successfully configured authentication on switch"
changed:
  description: Whether the module made changes
  returned: always
  type: bool
  sample: true
"""

from ansible.module_utils.basic import AnsibleModule

# Import the ZTP utility functions
try:
    from ansible.module_utils.aoscx_ztp import connect_ztp_device
    HAS_ZTP_UTILS = True
except ImportError:
    try:
        # Try alternative import path for collection
        from ansible_collections.arubanetworks.aoscx.plugins.module_utils.aoscx_ztp import connect_ztp_device
        HAS_ZTP_UTILS = True
    except ImportError:
        HAS_ZTP_UTILS = False


def main():
    """Main module execution."""

    module_args = dict(
        hostname=dict(type="str", required=True),
        username=dict(type="str", required=False, default="admin"),
        password=dict(type="str", required=True, no_log=True),
    )

    result = dict(
        changed=False,
        msg=""
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    if not HAS_ZTP_UTILS:
        module.fail_json(
            msg="Could not import aoscx_ztp module. "
                "Ensure the aoscx_ztp.py file is in the module_utils directory."
        )

    hostname = module.params["hostname"]
    username = module.params["username"]
    password = module.params["password"]

    try:
        # Attempt to connect and configure the ZTP device
        connect_ztp_device(module, hostname, username, password)

        # If we get here, the connection was successful
        result["changed"] = True
        result["msg"] = f"Successfully configured authentication on switch {hostname}"

        module.exit_json(**result)

    except Exception as e:
        module.fail_json(
            msg=f"Failed to configure authentication on {hostname}: {str(e)}",
            **result
        )


if __name__ == "__main__":
    main()
