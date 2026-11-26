<div align="center">
  <img src=".github/resources/logo.png" height="180px" width="auto" alt="rss temple logo">
  <br />
  <h2 style="font-size: 32px;">
    RSS Temple
  </h2>

  <h3 style="font-size: 25px;">
    A fast, powerful, self-hostable RSS reader.
  </h3>
  <br/>

[![license-badge-img]][license-badge]
[![Docker][docker-pulls-badge-img]][docker-pulls-badge]

  </div>
</div>

<div align="center">
  Go to the <a href="https://github.com/murrple-1/rss_temple">RSS Temple repo</a> for installation and usage instructions.
</div>

## Hardening the server

This collection opens only SSH, 80 and 443 in the firewall. It does not harden the rest of the OS or SSH. We
recommend that you also run the [DevSec hardening](https://github.com/dev-sec/ansible-collection-hardening) roles
on the server. Run them before the `pre_rss_temple` playbook, and again whenever you like:

```bash
ansible-galaxy collection install devsec.hardening
ansible-playbook --inventory <your inventory> harden.yml
```

`harden.yml`:

```yaml
---
- name: Harden Linux servers
  hosts: all
  become: true
  roles:
    - devsec.hardening.os_hardening
    - devsec.hardening.ssh_hardening
  vars:
    sysctl_overwrite:
      # Docker needs IP forwarding to route container traffic. os_hardening turns it off by default.
      net.ipv4.ip_forward: 1
```

Keep the `net.ipv4.ip_forward: 1` override. Without it, the containers can't be reached and the sites go down.

Before you run it, know that `ssh_hardening` changes how you log in:

- Root login and password login are disabled. Make sure that you can log in as a non-root user with sudo and an
  SSH key before you run it. The Terraform in
  [terraform-rss-temple](https://github.com/murrple-1/terraform-rss-temple) already sets the server up like this.
- TCP forwarding is disabled (`ssh_allow_tcp_forwarding: "no"`). If you use an SSH tunnel to reach the server, set
  it to `"yes"`.
- Only 2 authentication attempts are allowed (`ssh_max_auth_retries: 2`). If your SSH agent holds many keys, use
  `IdentitiesOnly yes` in your SSH config or the login can fail.

Keep an SSH session open while the first run applies, so that you can undo a change that locks you out.

## Development

The playbooks refer to the roles by their collection names (`murrple_1.rss_temple.<role>`), so they run against the installed collection, not the files in this checkout. To try local changes, install the checkout over any existing copy first:

```bash
ansible-galaxy collection install . --force
ansible-playbook --connection=local --inventory localhost, murrple_1.rss_temple.rss_temple
```

[license-badge-img]: https://img.shields.io/github/license/murrple-1/ansible-collection-rss-temple?style=for-the-badge&color=a32d2a
[license-badge]: LICENSE
[docker-pulls-badge-img]: https://img.shields.io/docker/pulls/murraychristopherson/rss_temple?style=for-the-badge&label=pulls
[docker-pulls-badge]: https://hub.docker.com/r/murraychristopherson/rss_temple
