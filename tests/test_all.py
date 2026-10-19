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
THU = lambda h, m: datetime(2026, 10, 22, h, m, tzinfo=DHAKA)


class SafetyTests(unittest.TestCase):
    def test_crisis_en(self): self.assertEqual(classify("I want to die")["label"], "crisis")
    def test_crisis_banglish(self): self.assertEqual(classify("ami more jabo")["label"], "crisis")
    def test_cheating(self): self.assertEqual(classify("write my assignment")["label"], "cheating")
    def test_safe(self): self.assertEqual(classify("room number of Nyme Ahmed")["label"], "safe")
    def test_crisis_not_answered_by_bot(self):
        r = BOT.handle("I want to die")
        self.assertEqual(r["intent"], "safety_escalation")
        self.assertIn("999", r["reply"])


class FacultyTests(unittest.TestCase):
    def test_room_and_status(self):
        r = BOT.handle("Nyme Ahmed madam er room number ki?", SUN(8, 0))
        self.assertEqual(r["intent"], "faculty")
        self.assertIn("DN0123", r["reply"]); self.assertIn("In class until 10:20", r["reply"])
    def test_spelling_variant(self):
        f, _ = BOT.faculty.find("niyme ahmed room"); self.assertEqual(f["id"], "F22")
    def test_full_name_beats_shared_name(self):
        f, _ = BOT.faculty.find("Aminun Nahar"); self.assertEqual(f["id"], "F21")
    def test_ambiguous_name_asks(self):
        r = BOT.handle("Nahar madam room", SUN(8, 0)); self.assertIn("more than one", r["reply"])
    def test_office_hour_now(self):
        r = BOT.handle("Is Aminun Nahar madam free now?", SUN(13, 0)); self.assertIn("In office hour until 14:00", r["reply"])
    def test_next_office_hour(self):
        f, _ = BOT.faculty.find("Nyme Ahmed"); n = BOT.faculty.next_office_hour(f, SUN(8, 0))
        self.assertEqual((n["when"], n["start"]), ("today", "10:20"))
    def test_admin_hour(self):
        f, _ = BOT.faculty.find("Nyme Ahmed")
        self.assertEqual(BOT.faculty.status(f, THU(13, 0))["state"], "admin")
    def test_no_timetable_is_not_guessed(self):
        r = BOT.handle("Anwarul Kabir room", SUN(8, 0))
        self.assertIn("DNO -216", r["reply"]); self.assertIn("timetable isn't available", r["reply"])
    def test_on_leave(self):
        r = BOT.handle("Rezwan Ahmed room", SUN(8, 0)); self.assertIn("on leave", r["reply"])
    def test_no_office_hours_listed(self):
        r = BOT.handle("Dipta Gomes room", SUN(8, 0)); self.assertIn("No office hours are listed", r["reply"])
    def test_unknown_name(self):
        r = BOT.handle("Zxqwv sir kothay?"); self.assertNotIn("sits in room", r["reply"])
    def test_no_phone_leak(self):
        from core.safety import output_guard
        self.assertIn("can't share", output_guard("call 01712345678"))
    def test_data_is_real_only(self):
        self.assertTrue(all(f["source"] == "real" for f in BOT.faculty.faculty.values()))


class KnowledgeTests(unittest.TestCase):
    def test_cgpa(self): self.assertIn("credit", BOT.handle("How is CGPA calculated?")["reply"].lower())
    def test_unknown_says_not_sure(self):
        self.assertIn("not sure", BOT.handle("what is the weather on mars purple banana")["reply"].lower())
    def test_stress_adds_support(self):
        self.assertIn("pressure", BOT.handle("I feel stressed about final exam")["reply"].lower())


if __name__ == "__main__":
    unittest.main()
