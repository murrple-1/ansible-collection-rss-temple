from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils.common.text.converters import to_text

# Order matters: backslashes first, so the escapes added after aren't escaped again
_ESCAPES = (
    ("\\", "\\\\"),
    ('"', '\\"'),
    ("$", "\\$"),
    ("\n", "\\n"),
    ("\r", "\\r"),
)


def dotenv_quote(value):
    """Quote a value for a Docker Compose `.env` file, so it reads back exactly as given.

    Compose's `.env` parser is not a shell: single-quoted values can't contain `'` at all (so `quote`'s
    `'"'"'` makes the whole file unreadable), and unquoted values treat ` #` as a comment and `$` as
    interpolation. Double-quoted values with `\\`, `"` and `$` escaped round-trip anything.
    """
    value = to_text(value)
    for old, new in _ESCAPES:
        value = value.replace(old, new)
    return '"' + value + '"'


class FilterModule(object):
    def filters(self):
        return {"dotenv_quote": dotenv_quote}
