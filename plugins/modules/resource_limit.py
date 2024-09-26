#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: resource_limit
short_description: Manages resource limits on Apache CloudStack based clouds.
description:
    - Manage limits of resources for domains, accounts and projects.
author: René Moser (@resmo)
version_added: 0.1.0
options:
  resource_type:
    description:
      - Type of the resource.
    type: str
    required: true
    choices:
      - instance
      - ip_address
      - volume
      - snapshot
      - template
      - network
      - vpc
      - cpu
      - memory
      - primary_storage
      - secondary_storage
    aliases: [ type ]
  limit:
    description:
      - Maximum number of the resource.
      - Default is unlimited C(-1).
    type: int
    default: -1
    aliases: [ max ]
  domain:
    description:
      - Domain the resource is related to.
    type: str
  account:
    description:
      - Account the resource is related to.
    type: str
  project:
    description:
      - Name of the project the resource is related to.
    type: str
extends_documentation_fragment:
- ngine_io.cloudstack.cloudstack
"""

EXAMPLES = """
- name: Update a resource limit for instances of a domain
  ngine_io.cloudstack.resource_limit:
    type: instance
    limit: 10
    domain: customers

- name: Update a resource limit for instances of an account
  ngine_io.cloudstack.resource_limit:
    type: instance
    limit: 12
    account: moserre
    domain: customers
"""

RETURN = """
---
recource_type:
  description: Type of the resource
  returned: success
  type: str
  sample: instance
limit:
  description: Maximum number of the resource.
  returned: success
  type: int
  sample: -1
domain:
  description: Domain the resource is related to.
  returned: success
  type: str
  sample: example domain
account:
  description: Account the resource is related to.
  returned: success
  type: str
  sample: example account
project:
  description: Project the resource is related to.
  returned: success
  type: str
  sample: example project
"""

# import cloudstack common
from ansible.module_utils.basic import AnsibleModule

from ..module_utils.cloudstack import AnsibleCloudStack, cs_argument_spec, cs_required_together

RESOURCE_TYPES = {
    "instance": 0,
    "ip_address": 1,
    "volume": 2,
    "snapshot": 3,
    "template": 4,
    "network": 6,
    "vpc": 7,
    "cpu": 8,
    "memory": 9,
    "primary_storage": 10,
    "secondary_storage": 11,
}


class AnsibleCloudStackResourceLimit(AnsibleCloudStack):
    """AnsibleCloudStackResourceLimit"""

    def __init__(self, module):
        super(AnsibleCloudStackResourceLimit, self).__init__(module)
        self.returns = {
            "max": "limit",
        }

    def get_resource_type(self):
        resource_type = self.module.params.get("resource_type")
        return RESOURCE_TYPES.get(resource_type)

    def get_resource_limit(self):
        args = {
            "account": self.get_account(key="name"),
            "domainid": self.get_domain(key="id"),
            "projectid": self.get_project(key="id"),
            "resourcetype": self.get_resource_type(),
        }
        resource_limit = self.query_api("listResourceLimits", **args)
        if resource_limit:
            if "limit" in resource_limit["resourcelimit"][0]:
                resource_limit["resourcelimit"][0]["limit"] = int(resource_limit["resourcelimit"][0])
            return resource_limit["resourcelimit"][0]
        self.module.fail_json(msg="Resource limit type '%s' not found." % self.module.params.get("resource_type"))

    def update_resource_limit(self):
        resource_limit = self.get_resource_limit()

        args = {
            "account": self.get_account(key="name"),
            "domainid": self.get_domain(key="id"),
            "projectid": self.get_project(key="id"),
            "resourcetype": self.get_resource_type(),
            "max": self.module.params.get("limit", -1),
        }

        if self.has_changed(args, resource_limit):
            self.result["changed"] = True
            if not self.module.check_mode:
                res = self.query_api("updateResourceLimit", **args)
                resource_limit = res["resourcelimit"]
        return resource_limit

    def get_result(self, resource):
        self.result = super(AnsibleCloudStackResourceLimit, self).get_result(resource)
        self.result["resource_type"] = self.module.params.get("resource_type")
        return self.result


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(
        dict(
            resource_type=dict(required=True, choices=list(RESOURCE_TYPES.keys()), aliases=["type"]),
            limit=dict(default=-1, aliases=["max"], type="int"),
            domain=dict(),
            account=dict(),
            project=dict(),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec, required_together=cs_required_together(), supports_check_mode=True)

    acs_resource_limit = AnsibleCloudStackResourceLimit(module)
    resource_limit = acs_resource_limit.update_resource_limit()
    result = acs_resource_limit.get_result(resource_limit)
    module.exit_json(**result)


if __name__ == "__main__":
    main()