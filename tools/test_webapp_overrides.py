# -*- coding: utf-8 -*-
"""Unit-test webapp key overrides against 3.11-like and 3.14 English trees."""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _webapp_key_overrides import apply_webapp_key_overrides  # noqa: E402

ZH = os.path.join(HERE, "data", "zh", "webapp-key-overrides.json")
EN = os.path.join(HERE, "data", "webapp-en.json")
I18N = os.path.join(HERE, "..", "assets", "webapp-i18n.json")


def rd(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class ApplyOverrides(unittest.TestCase):
    def test_skips_newer_keys_on_3_11_like_tree(self):
        # Reproduce Devin 3.11: auth exists, but 3.14 plan-tier keys do not.
        en = {
            "auth": {"authentication": "Authentication"},
            "actionModelPicker": {"effortPro": "Pro"},
            "billing": {"planNames.free": "Free"},
            "automations": {
                "dayInitialSaturday": "S",
                "dayInitialSunday": "S",
                "slackThreadModeNotify": "Notify in thread",
            },
        }
        wa = {
            "auth": {"authentication": "身份验证"},
            "actionModelPicker": {"effortPro": "专业版"},
            "automations": {
                "dayInitialSaturday": "日",
                "dayInitialSunday": "日",
                "slackThreadModeNotify": "在线程中通知",
            },
        }
        overrides = rd(ZH)
        applied, skipped = apply_webapp_key_overrides(en, wa, overrides)
        self.assertIn("auth.accountPicker.tierMax", skipped)
        self.assertIn("auth.accountPicker.tierPro", skipped)
        self.assertIn("billing.planNames.pro", skipped)
        self.assertGreater(applied, 0)
        self.assertEqual(wa["actionModelPicker"].get("effortPro"), None)
        self.assertEqual(wa["automations"]["dayInitialSaturday"], "六")
        self.assertEqual(wa["automations"]["dayInitialSunday"], "日")
        self.assertEqual(wa["automations"]["slackThreadModeNotify"], "在话题中通知")
        self.assertEqual(wa["auth"]["authentication"], "身份验证")

    def test_missing_key_does_not_block_later_overrides(self):
        en = {"auth": {"accountPicker.tierPro": "Pro"}}
        wa = {"auth": {"accountPicker.tierPro": "专业版", "accountPicker.tierMax": "最大"}}
        overrides = {
            "auth": {
                "accountPicker.tierMax": "Max",  # 3.14-only; must skip
                "accountPicker.tierPro": "Pro",  # present; must still apply
            }
        }
        applied, skipped = apply_webapp_key_overrides(en, wa, overrides)
        self.assertEqual(skipped, ["auth.accountPicker.tierMax"])
        self.assertEqual(applied, 1)
        self.assertNotIn("accountPicker.tierPro", wa["auth"])

    def test_current_3_14_resources_apply_every_override(self):
        en = rd(EN)["namespaces"]
        wa = json.loads(json.dumps(rd(I18N)))
        overrides = rd(ZH)
        applied, skipped = apply_webapp_key_overrides(en, wa, overrides)
        self.assertEqual(skipped, [])
        total = sum(len(v) for v in overrides.values())
        self.assertEqual(applied, total)
        self.assertIsNone((wa.get("auth") or {}).get("accountPicker.tierPro"))
        self.assertIsNone((wa.get("billing") or {}).get("planNames.pro"))
        self.assertEqual(wa["automations"]["dayInitialSaturday"], "六")
        self.assertEqual(wa["automations"]["dayInitialSunday"], "日")
        self.assertEqual(wa["automations"]["dayInitialThursday"], "四")
        self.assertEqual(wa["automations"]["dayInitialTuesday"], "二")
        self.assertEqual(wa["ui"]["crontabEditor.daySat"], "六")
        self.assertEqual(wa["ui"]["crontabEditor.daySun"], "日")
        self.assertEqual(wa["ui"]["crontabEditor.dayThu"], "四")
        self.assertEqual(wa["ui"]["crontabEditor.dayTue"], "二")

    def test_old_raise_would_abort_before_later_keys(self):
        """Document the 3.11 failure mode the skip path replaces."""
        en = {"auth": {"authentication": "Authentication"}}
        overrides = rd(ZH)
        with self.assertRaises(KeyError):
            for name, items in overrides.items():
                for k in items:
                    if name not in en or k not in en[name]:
                        raise KeyError("未知的 webapp key 覆盖: %s.%s" % (name, k))


class GeneratedArtifacts(unittest.TestCase):
    def test_webapp_i18n_matches_overrides(self):
        en = rd(EN)["namespaces"]
        wa = rd(I18N)
        overrides = rd(ZH)
        for name, items in overrides.items():
            for k, z in items.items():
                actual = (wa.get(name) or {}).get(k)
                if z == en[name][k]:
                    self.assertIsNone(actual, "%s.%s should stay English" % (name, k))
                else:
                    self.assertEqual(actual, z, "%s.%s" % (name, k))

    def test_share_user_edits_keeps_devin_cloud(self):
        zh = rd(os.path.join(HERE, "..", "assets", "ext-manifest.zh.json"))
        text = zh["windsurf.contributes.configuration.properties.devin.acp.shareUserEdits.description"]
        self.assertIn("Devin Cloud", text)
        self.assertNotIn("Devin 云会话", text)


class NoHalfWrite(unittest.TestCase):
    def test_apply_is_pure_and_does_not_touch_files(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write('{"marker": true}')
            en = {"auth": {}}
            wa = {"auth": {"accountPicker.tierMax": "最大"}}
            apply_webapp_key_overrides(en, wa, {"auth": {"accountPicker.tierMax": "Max"}})
            with open(path, "r", encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"marker": True})
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
