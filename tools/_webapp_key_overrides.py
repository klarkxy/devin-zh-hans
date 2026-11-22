# -*- coding: utf-8 -*-
"""Apply exact webapp i18n key overrides. Safe to import; no I/O."""


def apply_webapp_key_overrides(en_ns, wa_ns, overrides):
    """Apply per-key overrides to the i18next tree.

    Keys absent from the current English resource tree are skipped so a
    rebuild against an older Devin (e.g. 3.11 missing 3.14 keys) still
    finishes instead of aborting mid-write. A value equal to the English
    original removes the key from wa_ns (keep the product/plan name).

    Mutates wa_ns in place. Returns (applied, skipped) where skipped is a
    list of "namespace.key" strings.
    """
    applied = 0
    skipped = []
    for name, items in overrides.items():
        for k, z in items.items():
            if name not in en_ns or k not in en_ns[name]:
                skipped.append("%s.%s" % (name, k))
                continue
            if z == en_ns[name][k]:
                if name in wa_ns:
                    wa_ns[name].pop(k, None)
            else:
                wa_ns.setdefault(name, {})[k] = z
            applied += 1
    return applied, skipped
