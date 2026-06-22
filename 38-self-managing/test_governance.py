# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
# Offline test of the governance gates (no node needed — pure decision logic).

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "urirun" / "adapters" / "python"))

import governance

TRUSTED = {"package": "urirun-connector-x", "schemes": ["x"],
           "install": {"local": "/home/tom/github/if-uri/urirun-connector-x",
                       "git": "git+https://github.com/if-uri/urirun-connector-x.git"}}
UNTRUSTED = {"package": "urirun-connector-evil", "schemes": ["evil"],
             "install": {"git": "git+https://github.com/random-person/urirun-connector-evil.git"}}


class GovernanceTest(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.audit_log = []
        self.install = lambda client, c: (self.calls.append(c["package"]) or True)
        self.audit = self.audit_log.append

    def test_trusted_source_installs(self):
        p = governance.governed_provision(self.install, audit=self.audit)
        self.assertTrue(p(None, TRUSTED))
        self.assertEqual(self.calls, ["urirun-connector-x"])
        self.assertTrue(self.audit_log[-1]["ok"])

    def test_untrusted_blocked_without_approval(self):
        p = governance.governed_provision(self.install, audit=self.audit)
        self.assertFalse(p(None, UNTRUSTED))
        self.assertEqual(self.calls, [])                       # install never ran
        self.assertIn("allowlist", self.audit_log[-1]["decision"])

    def test_untrusted_allowed_with_approval(self):
        p = governance.governed_provision(self.install, approve=lambda c: True, audit=self.audit)
        self.assertTrue(p(None, UNTRUSTED))
        self.assertEqual(self.calls, ["urirun-connector-evil"])

    def test_failed_verify_blocks_serving(self):
        p = governance.governed_provision(self.install, verify_fn=lambda c: False, audit=self.audit)
        self.assertFalse(p(None, TRUSTED))
        self.assertEqual(self.calls, [])                       # verify gate stopped it
        self.assertIn("verify", self.audit_log[-1]["decision"])


if __name__ == "__main__":
    unittest.main()
