import json
import unittest
from pathlib import Path

from app.repository import DATA_DIR
from app.services.analyzer import local_problem_analysis
from app.services.auth import is_edu_tr_email, validate_registration
from app.services.matching import match_candidates, match_team
from app.services.talent import parse_talent_query, search_students


class AuthTests(unittest.TestCase):
    def test_school_email_is_accepted(self):
        self.assertTrue(is_edu_tr_email("ogrenci@itu.edu.tr"))
        self.assertTrue(validate_registration("ogrenci@itu.edu.tr", "student")["valid"])

    def test_normal_email_is_rejected_for_student(self):
        result = validate_registration("ogrenci@gmail.com", "student")
        self.assertFalse(result["valid"])
        self.assertIn(".edu.tr", result["errors"][0])

    def test_normal_email_is_allowed_for_industry_registration(self):
        self.assertTrue(validate_registration("firma@gmail.com", "industry")["valid"])


class AnalysisTests(unittest.TestCase):
    def test_guided_mode_asks_more_questions(self):
        entrepreneur = local_problem_analysis(
            "Enerji tüketimini tahmin eden bir yazılım geliştirmek istiyorum.",
            "entrepreneur",
        )
        expert = local_problem_analysis(
            "Enerji tüketimini tahmin eden bir yazılım geliştirmek istiyorum.",
            "rd_center",
        )
        self.assertGreater(len(entrepreneur["questions"]), len(expert["questions"]))
        self.assertEqual(expert["assistant_mode"], "expert")


class MatchingTests(unittest.TestCase):
    def test_different_problems_produce_different_academics(self):
        vibration = match_candidates(
            "CNC makinesinde rulman titreşimi ve kestirimci bakım için sensör verisi analizi.",
            "academic",
            top_k=1,
        )
        wastewater = match_candidates(
            "Tekstil atık suyunda membran ve adsorpsiyon ile deneysel arıtma optimizasyonu.",
            "academic",
            top_k=1,
        )
        food = match_candidates(
            "Gıda ambalajında sızdırmazlık, raf ömrü ve deneysel proses optimizasyonu.",
            "academic",
            top_k=1,
        )
        names = {
            vibration["results"][0]["candidate"]["name"],
            wastewater["results"][0]["candidate"]["name"],
            food["results"][0]["candidate"]["name"],
        }
        self.assertEqual(len(names), 3)
        self.assertEqual(wastewater["results"][0]["candidate"]["id"], "academic-002")
        self.assertEqual(food["results"][0]["candidate"]["id"], "academic-006")

    def test_team_has_academic_and_student(self):
        team = match_team(
            "Otomotiv pres hattında sac geri esnemesi için FEM simülasyonu ve deneysel doğrulama.",
            student_count=2,
        )
        self.assertTrue(team["team_ready"])
        self.assertGreaterEqual(len(team["academic_matches"]), 1)
        self.assertEqual(len(team["student_matches"]), 2)


class TalentSearchTests(unittest.TestCase):
    def test_natural_language_student_search(self):
        filters = parse_talent_query(
            "İTÜ Makine Mühendisliği 4. sınıf SolidWorks bilen İstanbul'da stajyer bul"
        )
        results = search_students(filters, top_k=5)
        self.assertIn("İstanbul Teknik Üniversitesi", filters["universities"])
        self.assertIn("SolidWorks", filters["skills"])
        self.assertEqual(results[0]["candidate"]["id"], "student-003")


class FixtureTests(unittest.TestCase):
    def test_json_fixtures_are_valid(self):
        for filename in ("candidates.json", "problems.json"):
            with (DATA_DIR / filename).open(encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertIsInstance(payload, list)
            self.assertGreater(len(payload), 0)


if __name__ == "__main__":
    unittest.main()

