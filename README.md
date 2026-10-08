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
