"""Run: python -m unittest discover tests -v"""
import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.assistant import Assistant
from core.faculty import DHAKA
from core.safety import classify

BOT = Assistant()
# Sunday 2026-10-18 is a workday in Bangladesh
SUN = lambda h, m: datetime(2026, 10, 18, h, m, tzinfo=DHAKA)


class SafetyTests(unittest.TestCase):
    def test_crisis_en(self): self.assertEqual(classify("I want to die")["label"], "crisis")
    def test_crisis_banglish(self): self.assertEqual(classify("ami more jabo")["label"], "crisis")
    def test_cheating(self): self.assertEqual(classify("write my assignment")["label"], "cheating")
    def test_safe(self): self.assertEqual(classify("room number of Nazib sir")["label"], "safe")
    def test_crisis_not_answered_by_bot(self):
        r = BOT.handle("I want to die")
        self.assertEqual(r["intent"], "safety_escalation")
        self.assertIn("999", r["reply"])


class FacultyTests(unittest.TestCase):
    def test_banglish_name(self):
        r = BOT.handle("Nazib sir er room number ki?", SUN(8, 0))
        self.assertEqual(r["intent"], "faculty"); self.assertIn("D-0405", r["reply"])
    def test_typo_name(self):
        f, _ = BOT.faculty.find("najeeb sir room"); self.assertEqual(f["id"], "F01")
    def test_unknown(self):
        r = BOT.handle("Zxqwv sir kothay?"); self.assertNotIn("D-0", r["reply"])
    def test_no_phone_leak(self):
        from core.safety import output_guard
        self.assertIn("can't share", output_guard("call 01712345678"))
    def test_next_office_hour_exists(self):
        f, _ = BOT.faculty.find("Rafiul"); self.assertIsNotNone(BOT.faculty.next_office_hour(f, SUN(8, 0)))


class KnowledgeTests(unittest.TestCase):
    def test_cgpa(self): self.assertIn("credit", BOT.handle("How is CGPA calculated?")["reply"].lower())
    def test_unknown_says_not_sure(self):
        self.assertIn("not sure", BOT.handle("what is the weather on mars purple banana")["reply"].lower())
    def test_stress_adds_support(self):
        self.assertIn("pressure", BOT.handle("I feel stressed about final exam")["reply"].lower())


if __name__ == "__main__":
    unittest.main()
