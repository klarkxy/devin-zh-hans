# -*- coding: utf-8 -*-
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open(r"H:\Archive\devin-zh-hans\tools\data\zh\webapp\w31.json", encoding="utf-8"))
probes = [
    'No channel mappings defined. Click "New mapping" to add one.',
    'No channels matching "{{searchQuery}}"',
    "No depots or streams found. Enter a path manually or check this account\u2019s permissions.",
    'No replay found for "{{id}}".',
    'No more next children',
    'No members yet, so no one on the team can use the Cyber Verification Program',
    'No type: {{total}}',
    "Next \u00b7 UTC",
    'No profile',
    'No escrow',
]
for k in probes:
    print(repr(k))
    print("   ->", d.get(k, "<<MISSING>>"))
print("total entries:", len(d))
print("first key:", repr(next(iter(d))))
print("last key :", repr(list(d)[-1]))
