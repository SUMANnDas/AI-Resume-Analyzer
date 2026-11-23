"""Regression tests for ResumeLens resume and role analysis."""

from __future__ import annotations

import unittest

from resume_parser_local import analyze_job_match, analyze_resume_text, find_skills


class SkillNormalizationTests(unittest.TestCase):
    def test_common_skill_variants_are_normalized(self) -> None:
        found = find_skills("JS, ReactJS, NodeJS, Postgres, K8s, GCP, and PowerBI")

        self.assertEqual(
            set(found),
            {"power bi", "google cloud", "postgresql", "javascript", "react", "node.js", "kubernetes"},
        )

    def test_role_title_contributes_recognized_role_skill(self) -> None:
        match = analyze_job_match(
            ["data analysis"],
            "Use data analytics and SQL to build reports.",
            {"score": 80, "contact_signals": {"email": True}},
            job_title="Senior Data Analyst",
        )

        self.assertIn("data analysis", match["required_skills"])
        self.assertNotIn("data analytics", match["required_skills"])
        self.assertNotIn("analytics", match["required_skills"])
        self.assertIn("data analysis", match["matched_skills"])


class RoleScoringTests(unittest.TestCase):
    def make_resume(self) -> dict[str, object]:
        return analyze_resume_text(
            """Jordan Example
jordan@example.com
Summary
Experience
Education
Skills
Projects
Certifications
Achievements
Python SQL
""",
            page_count=1,
        )

    def test_score_components_and_what_if_projection(self) -> None:
        resume = self.make_resume()

        match = analyze_job_match(["python", "sql"], "Python SQL Tableau", resume)

        self.assertEqual(match["required_skills"], ["tableau", "python", "sql"])
        self.assertEqual(match["coverage"], 67)
        self.assertEqual(match["score_components"]["structure_coverage"], 100)
        self.assertEqual(match["score_components"]["keyword_coverage"], 67)
        self.assertEqual(match["ats_score"], 70)
        self.assertEqual(match["projected_score"], 93)
        self.assertEqual(match["potential_score_gain"], 23)

    def test_empty_requirements_do_not_divide_by_zero(self) -> None:
        match = analyze_job_match(["python"], "A role description with no vocabulary terms.", self.make_resume())

        self.assertEqual(match["required_skills"], [])
        self.assertEqual(match["coverage"], 0)
        self.assertEqual(match["matched_skills"], [])


if __name__ == "__main__":
    unittest.main()
