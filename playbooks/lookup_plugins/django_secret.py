from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
  name: django_secret
  author: Murray Christopherson <murray@gray-os.com>
  version_added: "1.0.0"
  short_description: generate or retrive a Django SECRET_KEY
  description:
      - This lookup generates or retrieves a Django SECRET_KEY value from a provided file.
      - Very similar to `ansible.builtin.password`.
  options:
    _terms:
      description: path(s) of files to read
      required: True
    length:
      description: number of characters per secret
      type: int
      default: 50
      ini:
        - section: django_secret_lookup
          key: length
    chars:
      description: string characters to use in secret
      type: str
      default: 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
      ini:
        - section: django_secret_lookup
          key: chars
"""

EXAMPLES = """
- name: create a random SECRET_KEY
  ansible.builtin.debug:
    msg: "SECRET_KEY: {{ lookup('django_secrets', inventory_hostname + '.django_secret') }}"
"""

RETURN = """
_raw:
  description:
    - a Django secret
  type: list
  elements: str
"""

import os
import secrets

from ansible.plugins.lookup import LookupBase
from ansible.utils.path import makedirs_safe
from ansible.utils.display import Display


display = Display()


def _read_secret_file(path):
    content = None

    if os.path.exists(path):
        with open(path, "r") as f:
            content = f.read().strip()

    return content


def _write_secret_file(path, content):
    pathdir = os.path.dirname(path)

    makedirs_safe(pathdir, mode=0o700)

    with open(path, "w") as f:
        f.write(content)

    os.chmod(path, 0o600)


class LookupModule(LookupBase):
    # inspired by https://humberto.io/blog/tldr-generate-django-secret-key/
    def run(self, terms, variables, **kwargs):
        self.set_options(var_options=variables, direct=kwargs)

        ret = []
        for term in terms:
            path = self._loader.path_dwim(term)

            display.debug("lookup term path: %s" % path)

            changed = False

            content = _read_secret_file(path)

            if not content:
                content = "".join(
                    secrets.choice(self.get_option("chars"))
                    for i in range(self.get_option("length"))
                )

                display.debug("secret generated: %s" % content)

                changed = True

            if changed and path != "/dev/null":
                _write_secret_file(path, content)

            ret.append(content)

        return ret
