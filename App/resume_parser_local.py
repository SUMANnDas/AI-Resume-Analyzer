"""Local, privacy-conscious PDF and keyword analysis for ResumeLens."""

from __future__ import annotations

import re
from io import BytesIO

from pdfminer.high_level import extract_text
from pdfminer.pdfpage import PDFPage


MAX_PDF_BYTES = 10 * 1024 * 1024
MAX_PDF_PAGES = 20

SKILL_TERMS = (
    "react native", "machine learning", "deep learning", "data science", "data analytics",
    "data analysis", "user experience", "user research", "project management", "product management",
    "power bi", "google cloud", "scikit-learn", "rest api", "react.js", "node.js", "next.js",
    "tailwind css", "material ui", "adobe xd", "c++", "c#", ".net", "ui/ux", "figma",
    "photoshop", "illustrator", "tensorflow", "pytorch", "keras", "pandas", "numpy", "excel",
    "tableau", "postgresql", "mongodb", "mysql", "sqlite", "javascript", "typescript", "python",
    "java", "kotlin", "swift", "flutter", "android", "ios", "html", "css", "react", "angular",
    "vue", "django", "flask", "fastapi", "streamlit", "php", "laravel", "wordpress", "node",
    "docker", "kubernetes", "aws", "azure", "linux", "git", "github", "sql", "api", "agile",
    "scrum", "statistics", "analytics", "machine vision", "computer vision", "nlp", "natural language processing",
    "data visualization", "data modeling", "etl", "spark", "hadoop", "airflow", "dbt", "snowflake",
    "redis", "elasticsearch", "graphql", "microservices", "unit testing", "pytest", "jenkins",
    "ci/cd", "terraform", "ansible", "wireframing", "prototyping", "accessibility",
    "communication", "leadership", "teamwork", "customer service", "sales", "marketing", "writing",
    "problem solving", "business analysis", "financial analysis", "research", "presentation",
)

EMAIL_PATTERN = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(?<!\w)(?:\+?\d[\d().\s-]{7,}\d)(?!\w)")
LINKEDIN_PATTERN = re.compile(r"(?:linkedin\.com/in/|linkedin\.com/company/)", re.IGNORECASE)
BULLET_PATTERN = re.compile(r"^\s*(?:[•●▪◦‣*–—-]|\d+[.)])\s+")
METRIC_PATTERN = re.compile(
    r"(?<!\w)(?:[$€£]\s*\d[\d,.]*(?:\s?[KMB])?|"
    r"\d[\d,.]*\s?(?:%|x|k|m|b)(?!\w)|"
    r"\d[\d,.]*\s+(?:users?|customers?|clients?|projects?|people|"
    r"team members?|employees?|hours?|weeks?|months?|years?|days?))",
    re.IGNORECASE,
)
ACTION_VERBS = frozenset(
    "accelerated achieved automated built collaborated created decreased delivered "
    "designed developed directed improved increased launched led maintained managed "
    "optimized organized reduced redesigned resolved scaled streamlined trained "
    "transformed upgraded wrote analyzed implemented introduced negotiated "
    "coordinated established generated migrated published saved secured supported "
    "tested validated".split()
)
FIRST_PERSON_PATTERN = re.compile(r"\b(?:i|me|my|mine|we|us|our|ours)\b", re.IGNORECASE)

SECTION_CONFIG = {
    "Summary": {
        "weight": 10,
        "headings": ("summary", "professional summary", "profile", "professional profile", "objective", "career objective"),
        "suggestion": "Add a concise 2–3 line introduction that connects your strengths to the target role.",
    },
    "Experience": {
        "weight": 20,
        "headings": ("experience", "work experience", "professional experience", "employment history", "work history"),
        "suggestion": "Describe outcomes with action verbs and measurable scope, time, or impact where you can support it.",
    },
    "Education": {
        "weight": 15,
        "headings": ("education", "education background", "academic background", "academic history"),
        "suggestion": "List relevant qualifications, institutions, and dates so readers can scan your background quickly.",
    },
    "Skills": {
        "weight": 15,
        "headings": ("skills", "technical skills", "core skills", "core competencies", "technical proficiencies"),
        "suggestion": "Group relevant tools and strengths under a clear skills heading, then support them in your experience.",
    },
    "Projects": {
        "weight": 15,
        "headings": ("projects", "selected projects", "key projects", "project experience", "portfolio"),
        "suggestion": "Add a small selection of projects with your contribution, tools used, and a concrete result.",
    },
    "Certifications": {
        "weight": 10,
        "headings": ("certifications", "certificates", "licenses and certifications", "certifications and licenses"),
        "suggestion": "Include current, role-relevant certifications with the issuer and completion date, if applicable.",
    },
    "Achievements": {
        "weight": 5,
        "headings": ("achievements", "awards", "honors", "honours"),
        "suggestion": "Highlight relevant awards or accomplishments when they add evidence to your application.",
    },
}

ROLE_CLUSTERS = {
    "Data & AI": {"python", "sql", "pandas", "numpy", "scikit-learn", "machine learning", "deep learning", "data science", "data analytics", "tableau", "power bi", "tensorflow", "pytorch"},
    "Software engineering": {"python", "java", "javascript", "typescript", "react", "angular", "vue", "node.js", "django", "flask", "fastapi", "c++", "c#", ".net", "git", "rest api"},
    "Cloud & DevOps": {"aws", "azure", "google cloud", "docker", "kubernetes", "linux", "terraform", "ansible", "jenkins", "ci/cd"},
    "Product & design": {"figma", "ui/ux", "user experience", "user research", "wireframing", "prototyping", "product management", "accessibility", "adobe xd"},
    "Business & operations": {"business analysis", "project management", "sales", "marketing", "financial analysis", "customer service", "excel", "communication", "leadership"},
}

# Common spellings in job descriptions and resumes. Normalize only well-known
# variants so the comparison remains understandable and auditable.
SKILL_ALIASES = (
    (re.compile(r"\bdata analytics\b", re.IGNORECASE), "data analysis"),
    (re.compile(r"\bdata analyst\b", re.IGNORECASE), "data analysis"),
    (re.compile(r"\bdata scientist\b", re.IGNORECASE), "data science"),
    (re.compile(r"\bbusiness analyst\b", re.IGNORECASE), "business analysis"),
    (re.compile(r"\bproduct manager\b", re.IGNORECASE), "product management"),
    (re.compile(r"\bproject manager\b", re.IGNORECASE), "project management"),
    (re.compile(r"\bjs\b", re.IGNORECASE), "javascript"),
    (re.compile(r"\breactjs\b", re.IGNORECASE), "react"),
    (re.compile(r"\bnodejs\b", re.IGNORECASE), "node.js"),
    (re.compile(r"\bpostgres\b", re.IGNORECASE), "postgresql"),
    (re.compile(r"\bamazon web services\b", re.IGNORECASE), "aws"),
    (re.compile(r"\b(?:gcp|google cloud platform)\b", re.IGNORECASE), "google cloud"),
    (re.compile(r"\bk8s\b", re.IGNORECASE), "kubernetes"),
    (re.compile(r"\bsklearn\b", re.IGNORECASE), "scikit-learn"),
    (re.compile(r"\bpowerbi\b", re.IGNORECASE), "power bi"),
    (re.compile(r"\brestful apis?\b", re.IGNORECASE), "rest api"),
)


def _term_pattern(term: str) -> re.Pattern[str]:
    escaped = re.escape(term.casefold())
    return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", re.IGNORECASE)


def find_skills(text: str) -> list[str]:
    """Return vocabulary terms found at word boundaries, in stable display order."""
    normalized = text.casefold()
    for pattern, canonical in SKILL_ALIASES:
        normalized = pattern.sub(canonical, normalized)
    found = [term for term in SKILL_TERMS if _term_pattern(term).search(normalized)]
    # A compound technical term is a more useful signal than its shorter token.
    if "rest api" in found:
        found = [term for term in found if term not in {"api", "rest"}]
    if "node.js" in found and "node" in found:
        found.remove("node")
    if "react native" in found and "react" in found:
        found.remove("react")
    return found


def _normalize_heading(line: str) -> str:
    line = re.sub(r"\s+", " ", line.casefold()).strip()
    line = re.sub(r"\s*[:|•—–-]\s*$", "", line)
    return re.sub(r"[^a-z0-9 ]", "", line).strip()


def _heading_found(text: str, headings: tuple[str, ...]) -> bool:
    aliases = {_normalize_heading(item) for item in headings}
    for raw_line in text.splitlines():
        line = _normalize_heading(raw_line)
        if line in aliases:
            return True
        # PDFs sometimes place the first short item on the same line as a heading.
        if len(line.split()) <= 4 and any(line.startswith(alias + " ") for alias in aliases):
            return True
    return False


def analyze_resume_text(text: str, page_count: int) -> dict[str, object]:
    """Build non-identifying analysis signals from extracted resume text."""
    if not text.strip():
        raise ValueError("No selectable text was found. Try a text-based PDF; scanned image PDFs need OCR.")

    contact_signals = {
        "email": bool(EMAIL_PATTERN.search(text)),
        "phone": bool(PHONE_PATTERN.search(text)),
        "linkedin": bool(LINKEDIN_PATTERN.search(text)),
    }

    sections: dict[str, dict[str, int | bool]] = {}
    for name, config in SECTION_CONFIG.items():
        found = _heading_found(text, config["headings"])
        weight = int(config["weight"])
        sections[name] = {"found": found, "weight": weight, "earned": weight if found else 0}

    contact_points = round(10 * sum(contact_signals.values()) / len(contact_signals))
    sections["Contact signals"] = {"found": contact_points == 10, "weight": 10, "earned": contact_points}
    score = sum(int(section["earned"]) for section in sections.values())

    skills = find_skills(text)

    # These are lightweight writing signals. PDF extraction can alter line breaks,
    # so the UI describes them as clues to review rather than definitive findings.
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    bullet_lines = [BULLET_PATTERN.sub("", line).strip() for line in lines if BULLET_PATTERN.match(line)]
    action_led_lines = [
        line for line in lines
        if (words := re.findall(r"[a-z]+", BULLET_PATTERN.sub("", line).casefold()))
        and words[0] in ACTION_VERBS
    ]
    evidence_lines = bullet_lines or action_led_lines
    content_signals = {
        "bullet_lines": len(bullet_lines),
        "action_led_lines": len(action_led_lines),
        "quantified_lines": sum(bool(METRIC_PATTERN.search(line)) for line in evidence_lines),
        "long_lines": sum(len(line.split()) > 35 for line in evidence_lines),
        "first_person_mentions": len(FIRST_PERSON_PATTERN.findall(text)),
        "word_count": len(re.findall(r"\b[\w’'-]+\b", text)),
    }
    content_signals["reviewable_lines"] = len(evidence_lines)
    extraction_quality = "limited" if content_signals["word_count"] < 80 else "usable"

    role_signals = []
    for label, terms in ROLE_CLUSTERS.items():
        matches = sorted(terms.intersection(skills))
        if matches:
            role_signals.append({"label": label, "count": len(matches), "skills": matches})
    role_signals.sort(key=lambda item: (-int(item["count"]), str(item["label"])))

    suggestions = []
    for name, config in SECTION_CONFIG.items():
        if not sections[name]["found"]:
            suggestions.append({"section": name, "text": config["suggestion"], "priority": config["weight"]})
    if contact_points < 10:
        suggestions.append({
            "section": "Contact details",
            "text": "Check that your resume includes a professional email, a reliable phone number, and a profile link if you use one.",
            "priority": 10 - contact_points,
        })
    if evidence_lines and not content_signals["quantified_lines"]:
        suggestions.append({
            "section": "Measurable impact",
            "text": "No numbers were detected in the recognizable achievement lines. Where accurate, add the scale, time saved, volume, or result behind your work.",
            "priority": 18,
        })
    if bullet_lines and content_signals["action_led_lines"] < max(1, round(len(bullet_lines) * 0.4)):
        suggestions.append({
            "section": "Achievement bullets",
            "text": "Some bullet lines do not appear to start with a recognized action verb. Lead with the work you did, then add its result or scope.",
            "priority": 12,
        })
    if content_signals["long_lines"]:
        suggestions.append({
            "section": "Bullet readability",
            "text": f"{content_signals['long_lines']} recognizable achievement line(s) are longer than 35 words. Consider splitting or trimming them while keeping the outcome and context.",
            "priority": 8,
        })
    if content_signals["first_person_mentions"]:
        suggestions.append({
            "section": "Concise writing",
            "text": "First-person wording was detected. Check whether phrases such as “I” or “my” can be removed so each achievement starts with its contribution.",
            "priority": 4,
        })
    if extraction_quality == "limited":
        suggestions.append({
            "section": "Text extraction",
            "text": "Very little selectable text was extracted. Check the PDF text by selecting it, or export a text-based PDF; this review may miss content in image-only or complex layouts.",
            "priority": 20,
        })
    suggestions.sort(key=lambda item: (-int(item["priority"]), str(item["section"])))

    return {
        "score": score,
        "page_count": page_count,
        "sections": sections,
        "skills": skills,
        "role_signals": role_signals[:3],
        "contact_signals": contact_signals,
        "content_signals": content_signals,
        "extraction_quality": extraction_quality,
        "suggestions": suggestions,
    }


def analyze_resume_pdf(pdf_bytes: bytes) -> dict[str, object]:
    """Read and analyze a PDF from memory without writing it to disk."""
    if not pdf_bytes:
        raise ValueError("The uploaded PDF is empty.")
    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise ValueError("This PDF is larger than the 10 MB upload limit.")

    try:
        pages = sum(1 for _ in PDFPage.get_pages(BytesIO(pdf_bytes), maxpages=MAX_PDF_PAGES + 1, caching=False))
    except Exception as error:
        raise ValueError("This file could not be read as a valid PDF. Try exporting it again.") from error
    if pages > MAX_PDF_PAGES:
        raise ValueError(f"This PDF has more than {MAX_PDF_PAGES} pages. Upload a shorter resume PDF.")
    if pages == 0:
        raise ValueError("No pages were found in this PDF.")

    try:
        text = extract_text(BytesIO(pdf_bytes), maxpages=MAX_PDF_PAGES)
    except Exception as error:
        raise ValueError("Text could not be extracted from this PDF. Try exporting it again.") from error
    return analyze_resume_text(text, pages)


def analyze_job_match(
    resume_skills: list[str],
    job_description: str,
    resume_analysis: dict[str, object] | None = None,
    job_title: str = "",
) -> dict[str, object]:
    """Compare recognized terms and calculate a transparent ATS-style estimate."""
    required = find_skills(f"{job_title}\n{job_description}")
    resume_set = {skill.casefold() for skill in resume_skills}
    matched = [skill for skill in required if skill.casefold() in resume_set]
    missing = [skill for skill in required if skill.casefold() not in resume_set]
    coverage = round(len(matched) * 100 / len(required)) if required else 0
    analysis = resume_analysis or {}
    sections = analysis.get("sections", {})
    if isinstance(sections, dict) and sections:
        structural_sections = {
            name: item for name, item in sections.items()
            if name != "Contact signals" and isinstance(item, dict)
        }
        available_structure_points = sum(int(item.get("weight", 0)) for item in structural_sections.values())
        earned_structure_points = sum(int(item.get("earned", 0)) for item in structural_sections.values())
        structure_score = round(earned_structure_points * 100 / available_structure_points) if available_structure_points else 0
    else:
        structure_score = int(analysis.get("score", 0))
    contact_signals = analysis.get("contact_signals", {})
    if not isinstance(contact_signals, dict):
        contact_signals = {}
    contact_count = sum(bool(contact_signals.get(item)) for item in ("email", "phone", "linkedin"))
    contact_coverage = round(contact_count * 100 / 3)

    # This is an explainable heuristic, not a result from an employer's ATS.
    ats_score = round(coverage * 0.70 + structure_score * 0.20 + contact_coverage * 0.10)
    projected_score = round(100 * 0.70 + structure_score * 0.20 + contact_coverage * 0.10)
    if ats_score < 45:
        score_band = "Limited role alignment"
    elif ats_score < 75:
        score_band = "Developing role alignment"
    else:
        score_band = "Strong role alignment"

    return {
        "required_skills": required,
        "matched_skills": matched,
        "missing_skills": missing,
        "coverage": coverage,
        "ats_score": ats_score,
        "score_band": score_band,
        "projected_score": projected_score,
        "potential_score_gain": max(0, projected_score - ats_score),
        "score_components": {
            "keyword_coverage": coverage,
            "structure_coverage": structure_score,
            "contact_completeness": contact_coverage,
        },
        "score_weights": {
            "keyword_coverage": 70,
            "structure_coverage": 20,
            "contact_completeness": 10,
        },
    }
