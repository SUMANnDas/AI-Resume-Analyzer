"""ResumeLens: private, evidence-based resume and job match analysis."""

from __future__ import annotations

import hashlib
import html
import json
from datetime import datetime, timezone

import plotly.graph_objects as go
import streamlit as st

from resume_parser_local import analyze_job_match, analyze_resume_pdf


st.set_page_config(
    page_title="ResumeLens | Resume intelligence",
    page_icon="✳",
    layout="wide",
    initial_sidebar_state="expanded",
)


STYLE = """
<style>
:root { --ink:#15283f; --muted:#62738a; --teal:#0b8e82; --mint:#d9f2ec; --line:#e3eaf1; }
html, body, [class*="css"] { font-family:'Segoe UI',Arial,sans-serif; color:var(--ink); }
[data-testid="stAppViewContainer"] { background:#f5f8fb; }
[data-testid="stHeader"] { background:rgba(245,248,251,.88); }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#112940 0%,#142f45 100%); border-right:1px solid #203b51; }
[data-testid="stSidebar"] * { color:#e8f1f5; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { padding:9px 12px; border-radius:10px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background:#203c51; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#b8c9d2; }
[data-testid="stSidebar"] hr { border-color:#294358; }
.block-container { max-width:1320px; padding:2.3rem 2.8rem 4rem; }
h1,h2,h3 { font-family:'Segoe UI',Arial,sans-serif; letter-spacing:-.035em; color:#15283f; }
h1 { font-size:2.4rem!important; font-weight:800!important; }
h2 { font-size:1.55rem!important; font-weight:750!important; }
h3 { font-size:1.12rem!important; font-weight:700!important; }
.brand { display:flex; align-items:center; gap:11px; margin:14px 4px 8px; }
.brand-mark { display:grid; place-items:center; width:38px; height:38px; border-radius:12px; color:#103144!important; background:#91e4d0; font-size:21px; font-weight:800; }
.brand-name { color:white!important; font-family:'Segoe UI',Arial,sans-serif; font-weight:800; font-size:16px; letter-spacing:.02em; }
.brand-caption { color:#b8c9d2!important; font-size:11px; margin-top:-3px; }
.eyebrow { color:#0b8e82; font-size:11px; font-weight:800; letter-spacing:.14em; text-transform:uppercase; margin-bottom:8px; }
.hero { position:relative; overflow:hidden; padding:35px 38px; border-radius:24px; color:white; background:linear-gradient(115deg,#122b42 0%,#183f53 64%,#1c6a68 100%); box-shadow:0 18px 42px rgba(16,43,65,.12); }
.hero:after { content:''; position:absolute; width:310px; height:310px; border-radius:50%; right:-76px; top:-142px; border:1px solid rgba(198,255,239,.22); box-shadow:0 0 0 34px rgba(198,255,239,.035),0 0 0 72px rgba(198,255,239,.025); }
.hero-kicker { color:#a9dfd2; text-transform:uppercase; letter-spacing:.16em; font-size:11px; font-weight:800; }
.hero-title { font-family:'Segoe UI',Arial,sans-serif; font-size:35px; line-height:1.16; font-weight:800; color:#fff; max-width:740px; margin:14px 0 11px; letter-spacing:-.04em; }
.hero-copy { color:#d1e0e7; max-width:690px; line-height:1.65; font-size:15px; }
.hero-note { color:#b2dfd5; font-size:12px; margin-top:20px; }
.surface { background:white; border:1px solid var(--line); border-radius:18px; padding:21px 22px; box-shadow:0 5px 20px rgba(30,59,84,.035); height:100%; }
.surface-label { color:#708197; font-size:11px; font-weight:800; letter-spacing:.1em; text-transform:uppercase; margin-bottom:12px; }
.surface-title { color:#19334b; font-family:'Segoe UI',Arial,sans-serif; font-size:17px; font-weight:750; margin-bottom:8px; }
.surface-copy { color:#687b90; font-size:13px; line-height:1.6; }
.metric-card { border:1px solid var(--line); border-radius:17px; padding:17px 19px; background:white; min-height:112px; box-shadow:0 5px 18px rgba(30,59,84,.035); }
.metric-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin:12px 0; }
.metric-grid.three { grid-template-columns:repeat(3,minmax(0,1fr)); }
.feature-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px; margin-top:8px; }
.profile-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px; margin-top:8px; }
.metric-label { color:#708197; text-transform:uppercase; letter-spacing:.09em; font-size:10px; font-weight:800; }
.metric-value { color:#163149; font-family:'Segoe UI',Arial,sans-serif; font-size:27px; line-height:1.2; font-weight:800; margin:8px 0 3px; }
.metric-foot { color:#75869a; font-size:11px; }
.pill { display:inline-block; padding:6px 10px; border:1px solid #d4e9e5; border-radius:999px; background:#f1faf7; color:#13776e; margin:3px 4px 3px 0; font-size:12px; font-weight:600; }
.privacy { padding:13px 14px; border:1px solid #cfe9e3; border-radius:14px; background:#eaf7f4; color:#315f5a; font-size:12px; line-height:1.5; }
[data-testid="stSidebar"] .privacy { border-color:rgba(159,218,203,.2); background:rgba(255,255,255,.055); color:#d8e8eb; }
.section-head { margin-top:27px; }
.muted { color:#718198; font-size:13px; }
.small-note { color:#718198; font-size:11px; line-height:1.55; }
.check-list { display:flex; flex-direction:column; gap:8px; margin:8px 0 4px; }
.check-row { display:flex; justify-content:space-between; align-items:center; gap:12px; padding:10px 12px; border:1px solid #e7edf2; border-radius:11px; background:#fbfcfd; color:#294158; font-size:13px; }
.check-row span:last-child { color:#667b8f; font-size:11px; font-weight:700; white-space:nowrap; }
.check-row .check-found { color:#08766d!important; }
.recommendation { padding:13px 15px; margin:9px 0; border:1px solid #e5ebf0; border-left:3px solid #0b8e82; border-radius:12px; background:#fff; }
.recommendation-label { color:#0b8177; font-size:10px; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }
.recommendation-title { color:#19334b; font-weight:750; margin-top:5px; }
.recommendation-copy { color:#687b90; font-size:12px; line-height:1.55; margin-top:4px; }
.signal-note { padding:11px 13px; border-radius:11px; background:#f1f6f8; color:#536a7d; font-size:12px; line-height:1.55; margin-top:8px; }
div.stButton > button, div.stDownloadButton > button { border-radius:11px; font-weight:700; min-height:42px; }
div.stButton > button[kind="primary"] { border:0; background:#0b8e82; }
div.stButton > button[kind="primary"]:hover { background:#08766d; }
[data-testid="stFileUploader"] { border:1px dashed #9db5c4; border-radius:15px; background:#fbfdff; color:#243b53; }
[data-testid="stMetric"] { background:white; border:1px solid var(--line); border-radius:14px; padding:13px 16px; }
[data-testid="stAlert"] { border-radius:13px; }
@media(min-width:801px) and (max-width:1100px) { .block-container{padding-left:1.25rem;padding-right:1.25rem}.feature-grid,.profile-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.metric-grid,.metric-grid.three{grid-template-columns:repeat(2,minmax(0,1fr))} }
@media(max-width:800px) { .block-container{padding:1.2rem 1rem 3rem}.hero{padding:27px 23px}.hero-title{font-size:28px}h1{font-size:2rem!important}.feature-grid,.profile-grid,.metric-grid,.metric-grid.three{grid-template-columns:1fr} }
</style>
"""

st.markdown(STYLE, unsafe_allow_html=True)


def card_markup(label: str, title: str, copy: str) -> str:
    return (
        f'<div class="surface"><div class="surface-label">{html.escape(label)}</div>'
        f'<div class="surface-title">{html.escape(title)}</div>'
        f'<div class="surface-copy">{html.escape(copy)}</div></div>'
    )


def card(label: str, title: str, copy: str) -> None:
    st.markdown(card_markup(label, title, copy), unsafe_allow_html=True)


def metric_card_markup(label: str, value: str, foot: str) -> str:
    return (
        f'<div class="metric-card"><div class="metric-label">{html.escape(label)}</div>'
        f'<div class="metric-value">{html.escape(value)}</div>'
        f'<div class="metric-foot">{html.escape(foot)}</div></div>'
    )


def metric_card(label: str, value: str, foot: str) -> None:
    st.markdown(metric_card_markup(label, value, foot), unsafe_allow_html=True)


def page_heading(eyebrow: str, title: str, description: str) -> None:
    st.markdown(f'<div class="eyebrow">{html.escape(eyebrow)}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<p class="muted">{html.escape(description)}</p>', unsafe_allow_html=True)


def overview_page() -> None:
    st.markdown(
        """
        <div class="hero">
          <div class="hero-kicker">Resume intelligence workspace</div>
          <div class="hero-title">Make your next application<br>clearer and more targeted.</div>
          <div class="hero-copy">Get a practical structure audit, surface the skills already in your resume, and compare them with a role description.</div>
          <div class="hero-note">✳ &nbsp; Private by design &nbsp; · &nbsp; Evidence based &nbsp; · &nbsp; Ready in seconds</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    feature_cards = (
        ("01 · Audit", "Understand your resume", "Review section coverage, achievement writing signals, detected skills, and prioritized edits in one report."),
        ("02 · Compare", "Match a target role", "Estimate role-specific ATS alignment from skill overlap, resume structure, and contact signals."),
        ("03 · Improve", "Leave with a plan", "Use practical suggestions to guide your next revision, then export a privacy-safe audit or role comparison."),
    )
    st.markdown('<div class="feature-grid">' + "".join(card_markup(*item) for item in feature_cards) + '</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-head"></div>', unsafe_allow_html=True)
    page_heading("Start here", "A focused workflow", "Three steps from a PDF to a more deliberate application.")
    steps = (
        ("STEP 1", "Upload a text PDF", "Your document is read in memory and is not written to the project or a database."),
        ("STEP 2", "Review the evidence", "Check section headings, writing patterns, and skills the analyzer could detect. Treat each signal as a prompt to review."),
        ("STEP 3", "Tailor it to a role", "Compare the resume with a job description and focus on genuine experience that is currently underrepresented."),
    )
    st.markdown('<div class="feature-grid">' + "".join(card_markup(*item) for item in steps) + '</div>', unsafe_allow_html=True)

    result = st.session_state.get("resume_analysis")
    if result:
        st.markdown('<div class="section-head"></div>', unsafe_allow_html=True)
        st.subheader("Your current session")
        metrics = (
            ("Structure coverage", f"{result['score']} / 100", "Section checklist, not a hiring score"),
            ("Skills detected", str(len(result["skills"])), "From selectable PDF text"),
            ("Pages", str(result["page_count"]), "Current in-memory document"),
        )
        st.markdown('<div class="metric-grid three">' + "".join(metric_card_markup(*item) for item in metrics) + '</div>', unsafe_allow_html=True)
        st.caption("Your analysis stays available as you move between pages. Use Start a new audit to clear it.")

    if st.button("Open resume audit", type="primary", use_container_width=False):
        st.session_state["navigation"] = "Resume audit"
        st.rerun()


def render_resume_analysis(result: dict[str, object]) -> None:
    st.markdown('<div class="section-head"></div>', unsafe_allow_html=True)
    contacts = result["contact_signals"]
    count = sum(bool(value) for value in contacts.values())
    top_metrics = (
        ("Structure coverage", f"{result['score']} / 100", "Section checklist"),
        ("Skills detected", str(len(result["skills"])), "Keyword inventory"),
        ("Length", f"{result['page_count']} pages", "Text-based PDF"),
        ("Contact signals", f"{count} / 3", "Email · phone · LinkedIn"),
    )
    st.markdown('<div class="metric-grid">' + "".join(metric_card_markup(*item) for item in top_metrics) + '</div>', unsafe_allow_html=True)

    left, right = st.columns([1.1, 1], gap="large")
    with left:
        st.markdown('<div class="section-head"></div>', unsafe_allow_html=True)
        st.subheader("Section coverage checklist")
        st.caption("This checklist checks for section headings and contact signals. It does not judge writing quality.")
        sections = result["sections"]
        labels = list(sections)
        values = [sections[name]["earned"] for name in labels]
        maximums = [sections[name]["weight"] for name in labels]
        fig = go.Figure()
        fig.add_trace(go.Bar(y=labels, x=maximums, orientation="h", marker_color="#eaf0f4", name="Available points", hoverinfo="skip"))
        fig.add_trace(go.Bar(y=labels, x=values, orientation="h", marker_color="#0b8e82", name="Evidence found", hovertemplate="%{y}: %{x} checklist points<extra></extra>"))
        fig.update_layout(
            barmode="overlay", height=335, margin=dict(l=5, r=12, t=12, b=8),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Segoe UI, Arial, sans-serif", color="#63778c", size=12),
            xaxis=dict(range=[0, max(maximums) * 1.12], visible=False),
            yaxis=dict(autorange="reversed", gridcolor="rgba(0,0,0,0)"),
            legend=dict(orientation="h", y=-0.08, x=0),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        checklist = []
        for name, item in sections.items():
            found = bool(item["found"])
            status = "Detected" if found else "Review"
            checklist.append(
                '<div class="check-row"><span>' + html.escape(str(name)) + '</span>'
                + f'<span class="{"check-found" if found else ""}">{status} · {item["earned"]}/{item["weight"]} points</span></div>'
            )
        st.markdown('<div class="check-list">' + "".join(checklist) + "</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-head"></div>', unsafe_allow_html=True)
        st.subheader("Review priorities")
        suggestions = result["suggestions"]
        if suggestions:
            for index, item in enumerate(suggestions, 1):
                priority_label = "Review first" if index == 1 else "Next step"
                st.markdown(
                    '<div class="recommendation"><div class="recommendation-label">'
                    + f'{priority_label} · {index:02d}</div><div class="recommendation-title">'
                    + html.escape(str(item["section"])) + '</div><div class="recommendation-copy">'
                    + html.escape(str(item["text"])) + '</div></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.success("Every section in this checklist was detected. Review whether each one includes clear, role-relevant evidence.")

    st.markdown('<div class="section-head"></div>', unsafe_allow_html=True)
    st.subheader("Achievement and writing signals")
    st.caption("These checks look for patterns in extracted PDF lines. Line breaks can vary by PDF, so use them as review prompts rather than definitive judgments.")
    signals = result["content_signals"]
    reviewable = int(signals["reviewable_lines"])
    signal_data = (
        ("Impact lines with numbers", f'{signals["quantified_lines"]} / {reviewable}' if reviewable else "—", "Recognizable achievement lines with a number" if reviewable else "No achievement lines were reliably detected"),
        ("Action-led lines", str(signals["action_led_lines"]), "Lines beginning with a recognized action verb"),
        ("Long achievement lines", str(signals["long_lines"]), "Over 35 words; consider tightening"),
        ("First-person mentions", str(signals["first_person_mentions"]), "I / me / my / we / our wording"),
    )
    st.markdown('<div class="metric-grid">' + "".join(metric_card_markup(*item) for item in signal_data) + '</div>', unsafe_allow_html=True)
    if result["extraction_quality"] == "limited":
        st.warning("The PDF yielded very little selectable text. Some content checks may be incomplete; verify the document has selectable text or export it again.")
    else:
        st.markdown(
            f'<div class="signal-note">About {signals["word_count"]:,} words were extracted across '
            f'{result["page_count"]} page(s). These counts help explain what the rules could review; '
            'they are not a readability grade or an ATS score.</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-head"></div>', unsafe_allow_html=True)
    st.subheader("Skills found in the document")
    if result["skills"]:
        skill_markup = "".join(f'<span class="pill">{html.escape(skill)}</span>' for skill in result["skills"])
        st.markdown(skill_markup, unsafe_allow_html=True)
    else:
        st.info("No skills from the built-in vocabulary were found. The text may use different terminology, or the PDF may be image-only.")

    st.markdown('<div class="section-head"></div>', unsafe_allow_html=True)
    st.subheader("Profile signals")
    role_signals = result["role_signals"]
    role_cards = [
        ("Keyword cluster", f"{item['label']} · {item['count']} skill signals", "A broad pattern in the detected skills, not a predicted job title.")
        for item in role_signals
    ] or [("Keyword cluster", "No strong role cluster detected", "A broad pattern in the detected skills, not a predicted job title.")]
    st.markdown('<div class="profile-grid">' + "".join(card_markup(*item) for item in role_cards) + '</div>', unsafe_allow_html=True)

    report = {
        "product": "ResumeLens",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "structure_coverage": result["score"],
        "page_count": result["page_count"],
        "sections": result["sections"],
        "skills_detected": result["skills"],
        "role_signals": result["role_signals"],
        "contact_signals": result["contact_signals"],
        "content_signals": result["content_signals"],
        "extraction_quality": result["extraction_quality"],
        "suggestions": result["suggestions"],
        "note": "Rule-based checklist and text-pattern review. This is not an ATS score or hiring recommendation. Contact values, job description text, and resume text are excluded.",
    }
    st.download_button(
        "Download privacy-safe audit (JSON)",
        data=json.dumps(report, indent=2, ensure_ascii=False),
        file_name="resumelens-audit.json",
        mime="application/json",
        type="primary",
    )
    st.caption("The export contains detected skills and checklist results. It excludes the resume text and personal contact values.")


def _role_digest(title: str, description: str) -> str:
    if not description.strip():
        return ""
    role_input = f"{title.strip()}\0{description.strip()}"
    return hashlib.sha256(role_input.encode("utf-8")).hexdigest()


def _sync_role_inputs(page: str, title_key: str, details_key: str) -> None:
    if st.session_state.get("active_role_input_page") != page:
        st.session_state[title_key] = st.session_state.get("saved_target_job_title", "")
        st.session_state[details_key] = st.session_state.get("saved_target_job_details", "")
        st.session_state["active_role_input_page"] = page


def render_role_match(match: dict[str, object], title: str, resume: dict[str, object]) -> None:
    display_title = title.strip() or "Target role"
    st.markdown('<div class="section-head"></div>', unsafe_allow_html=True)
    st.subheader("Role alignment")
    st.caption(display_title)
    st.markdown(
        '<div class="signal-note">This is a transparent ATS-style estimate, not a score from an employer’s ATS and not a prediction of interview or hiring outcomes.</div>',
        unsafe_allow_html=True,
    )
    components = match["score_components"]
    score_metrics = (
        ("ATS match estimate", f"{match['ats_score']} / 100", str(match["score_band"])),
        ("Recognized skill coverage", f"{match['coverage']}%", f"{len(match['matched_skills'])} of {len(match['required_skills'])} role skills detected"),
        ("Structure checklist", f"{components['structure_coverage']}%", "Section coverage, excluding contact signals"),
        ("What-if estimate", f"{match['projected_score']} / 100", f"+{match['potential_score_gain']} points if gaps are genuinely evidenced"),
    )
    st.markdown('<div class="metric-grid">' + "".join(metric_card_markup(*item) for item in score_metrics) + '</div>', unsafe_allow_html=True)
    st.progress(match["ats_score"] / 100, text=f"{match['ats_score']} / 100 · {match['score_band']}")

    with st.expander("How this estimate is calculated"):
        st.markdown(
            f"- **Recognized skill coverage — 70%:** {components['keyword_coverage']}% of skills found in the title and details also appear in the resume’s detected skill list.\n"
            f"- **Resume structure — 20%:** {components['structure_coverage']}% from the section checklist, excluding contact signals.\n"
            f"- **Contact completeness — 10%:** {components['contact_completeness']}% based on whether email, phone, and LinkedIn signals were found.\n\n"
            "Alignment bands are heuristic: under 45 is limited, 45–74 is developing, and 75 or higher is strong. The what-if estimate assumes every currently missing recognized skill is already supported by real experience and can be represented in the resume. It is an illustration, not a guaranteed score change."
        )
    if resume.get("extraction_quality") == "limited":
        st.warning("The PDF yielded limited selectable text, so the skill overlap and estimate may miss resume content.")
    if match["missing_skills"]:
        st.markdown(
            '<div class="signal-note"><b>Suggested next step:</b> Review each missing term against your experience. If you can support it, describe that work naturally in the relevant section; do not add unsupported keywords.</div>',
            unsafe_allow_html=True,
        )
    elif match["required_skills"]:
        st.success("All recognized skills from this role description were detected in your resume.")

    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Skills found in both")
        if match["matched_skills"]:
            for skill in match["matched_skills"]:
                st.markdown(f"✓ &nbsp; {html.escape(skill)}", unsafe_allow_html=True)
        else:
            st.caption("No recognized skills overlap yet.")
    with right:
        st.subheader("Skills not detected")
        if match["missing_skills"]:
            for skill in match["missing_skills"]:
                st.markdown(f"＋ &nbsp; {html.escape(skill)}", unsafe_allow_html=True)
        else:
            st.caption("No recognized skill gaps found.")

    report = {
        "product": "ResumeLens",
        "target_role": display_title,
        "ats_match_estimate": match["ats_score"],
        "alignment_band": match["score_band"],
        "illustrative_what_if_score": match["projected_score"],
        "keyword_coverage_percent": match["coverage"],
        "score_components": match["score_components"],
        "score_weights_percent": match["score_weights"],
        "recognized_requirements": match["required_skills"],
        "matched_skills": match["matched_skills"],
        "not_detected": match["missing_skills"],
        "note": "Local vocabulary and checklist heuristic only. Not an employer ATS score, qualification assessment, or hiring prediction. Resume text, job description, and contact values are excluded.",
    }
    st.download_button(
        "Download role analysis (JSON)",
        data=json.dumps(report, indent=2, ensure_ascii=False),
        file_name="resumelens-role-analysis.json",
        mime="application/json",
        key="download_role_analysis",
    )


def audit_page() -> None:
    page_heading("Resume audit", "Make your resume fit the role", "Upload a resume, add the target job, and review a focused match report with clear next steps.")
    st.markdown(
        '<div class="privacy">🔒 <b>Private processing</b> · The PDF is processed in memory by this app and is not saved to a database or uploaded folder. For local use, run this app on your own computer.</div>',
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown('<div class="eyebrow">STEP 1 · YOUR RESUME</div>', unsafe_allow_html=True)
    generation = int(st.session_state.get("resume_upload_generation", 0))
    uploaded = st.file_uploader(
        "Upload a resume PDF",
        type=["pdf"],
        key=f"resume_upload_{generation}",
        help="Text-based PDF · maximum 10 MB and 20 pages · scanned image PDFs are not supported yet.",
        max_upload_size=10,
    )
    existing_result = st.session_state.get("resume_analysis")
    if st.button(
        "Start a new audit",
        disabled=uploaded is None and not existing_result,
        help="Clear the current resume analysis and role comparison.",
        key="start_new_audit",
    ):
        for key in (
            "resume_analysis",
            "job_match",
            "resume_file_name",
            "saved_target_job_title",
            "saved_target_job_details",
            "active_role_input_page",
            "audit_job_title_input",
            "audit_job_details_input",
            "match_job_title_input",
            "match_job_details_input",
        ):
            st.session_state.pop(key, None)
        st.session_state["resume_upload_generation"] = generation + 1
        st.rerun()

    if uploaded is None and not existing_result:
        st.markdown('<div class="section-head"></div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            card("STEP 2 · TARGET ROLE", "Add the job you want", "Enter the job title and description. The audit will compare recognized skills and estimate role alignment.")
        with c2:
            card("STEP 3 · REVIEW", "Get a practical report", "See the match estimate, skills detected in both, gaps to review, and your resume structure checklist.")
        return

    result = st.session_state.get("resume_analysis")
    if uploaded is not None:
        pdf_bytes = uploaded.getvalue()
        digest = hashlib.sha256(pdf_bytes).hexdigest()
    else:
        digest = ""
    if uploaded is not None and (not result or result.get("_digest") != digest):
        st.session_state.pop("resume_analysis", None)
        st.session_state.pop("job_match", None)
        try:
            with st.spinner("Reviewing the PDF text…"):
                result = analyze_resume_pdf(pdf_bytes)
            result["_digest"] = digest
            st.session_state["resume_analysis"] = result
            st.session_state["resume_file_name"] = uploaded.name
        except ValueError as error:
            st.session_state.pop("resume_analysis", None)
            st.error(str(error))
            return
        except Exception:
            st.session_state.pop("resume_analysis", None)
            st.error("This PDF could not be read. Try exporting it again as a text-based PDF.")
            return

    if result is None:
        st.info("Upload a resume PDF to continue.")
        return

    if uploaded is None:
        st.info(f"Using **{html.escape(str(st.session_state.get('resume_file_name', 'your saved resume')))}** from this session. Your analysis stays available when you switch pages.")
    if result["extraction_quality"] == "limited":
        st.warning(f"Limited text extracted · {result['page_count']} page{'s' if result['page_count'] != 1 else ''} · review the signals carefully")
    else:
        st.success(f"Resume reviewed · {result['page_count']} page{'s' if result['page_count'] != 1 else ''} · contact details are not displayed")

    st.markdown('<div class="section-head"></div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<div class="eyebrow">STEP 2 · TARGET ROLE</div>', unsafe_allow_html=True)
        st.subheader("What role are you applying for?")
        st.caption("Add the job title and paste its responsibilities or requirements. We’ll compare skills and show how the estimate is calculated.")
        _sync_role_inputs("audit", "audit_job_title_input", "audit_job_details_input")
        with st.form("audit_role_form"):
            role_title = st.text_input(
                "Job title",
                key="audit_job_title_input",
                max_chars=160,
                placeholder="e.g. Data Analyst",
            )
            role_description = st.text_area(
                "Job details or description",
                key="audit_job_details_input",
                height=190,
                max_chars=30000,
                placeholder="Paste the responsibilities, required skills, and qualifications…",
                help="Only recognized skill terms are compared. The full description stays in this browser session and is excluded from exports.",
            )
            run_role_audit = st.form_submit_button(
                "Analyze match",
                type="primary",
            )
    role_digest = _role_digest(role_title, role_description)
    if run_role_audit:
        if not role_description.strip():
            st.warning("Paste the job details before analyzing the match.")
        else:
            st.session_state["saved_target_job_title"] = role_title
            st.session_state["saved_target_job_details"] = role_description
            role_result = analyze_job_match(result["skills"], role_description, result, role_title)
            role_result["_source_digest"] = role_digest
            role_result["_resume_digest"] = result.get("_digest")
            st.session_state["job_match"] = role_result

    role_result = st.session_state.get("job_match")
    if role_result and (
        role_result.get("_source_digest") != role_digest
        or role_result.get("_resume_digest") != result.get("_digest")
    ):
        role_result = None
    if role_result:
        if not role_result["required_skills"]:
            st.warning("No skills from our built-in vocabulary were found in the title or job details. Add the requirements section, or check the vocabulary limits described in How it works.")
        else:
            render_role_match(role_result, role_title, result)

    st.markdown('<div class="section-head"></div>', unsafe_allow_html=True)
    with st.expander("View complete resume audit", expanded=False):
        st.caption("These document-wide checks complement the target-role estimate. Review the extracted text and suggestions before changing your resume.")
        render_resume_analysis(result)


def match_page() -> None:
    page_heading("Job match", "Estimate alignment with a target role", "Compare recognized skills, review match signals, and see an illustrative ATS-style score with practical next steps.")
    resume = st.session_state.get("resume_analysis")
    if not resume:
        st.info("Start with a resume audit. Your analysis will be available here for this session.")
        if st.button("Go to resume audit", type="primary"):
            st.session_state["navigation"] = "Resume audit"
            st.rerun()
        return

    _sync_role_inputs("match", "match_job_title_input", "match_job_details_input")
    with st.form("job_match_form"):
        role_title = st.text_input(
            "Job title",
            key="match_job_title_input",
            max_chars=160,
            placeholder="e.g. Data Analyst",
        )
        description = st.text_area(
            "Job details or description",
            key="match_job_details_input",
            height=250,
            max_chars=30000,
            placeholder="Paste the role responsibilities, requirements, and skills here…",
            help="Only recognized skill terms are used in the comparison. The description remains in this browser session and is excluded from exports.",
        )
        compare_role = st.form_submit_button(
            "Analyze role match",
            type="primary",
        )
    description_digest = _role_digest(role_title, description)
    if compare_role:
        if not description.strip():
            st.warning("Paste the job details before analyzing the match.")
        else:
            st.session_state["saved_target_job_title"] = role_title
            st.session_state["saved_target_job_details"] = description
            match = analyze_job_match(resume["skills"], description, resume, role_title)
            match["_source_digest"] = description_digest
            match["_resume_digest"] = resume.get("_digest")
            st.session_state["job_match"] = match

    match = st.session_state.get("job_match")
    if match and (
        match.get("_source_digest") != description_digest
        or match.get("_resume_digest") != resume.get("_digest")
    ):
        match = None
    if not match:
        st.markdown('<div class="section-head"></div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            card("Comparison method", "Transparent signals", "The estimate combines recognized skill overlap, resume section coverage, and contact-presence signals. Common skill spelling variants are normalized.")
        with c2:
            card("Use gaps carefully", "Add evidence, not buzzwords", "A missing term can reflect different wording or a skill outside the built-in vocabulary. Include it only when you can support it with real experience.")
        return

    st.markdown('<div class="section-head"></div>', unsafe_allow_html=True)
    if not match["required_skills"]:
        st.warning("No recognized skill terms were found in those job details. Try including the requirements or skills section.")
        return
    render_role_match(match, role_title, resume)


def method_page() -> None:
    page_heading("About ResumeLens", "Transparent analysis you can inspect", "A lightweight resume review tool that runs locally without an external AI service or database.")
    a, b = st.columns(2, gap="large")
    with a:
        card("01 · Extraction", "Read selectable PDF text", "pdfminer.six extracts text and page count. Contact fields are reduced to presence signals; their values are not shown or written to storage.")
    with b:
        card("02 · Evidence", "Match a fixed vocabulary", "A local keyword list detects common skills and normalizes a short list of common spelling variants. Section headings and writing patterns are checked as review signals.")
    c, d = st.columns(2, gap="large")
    with c:
        card("03 · Scoring", "Checklist coverage from 0 to 100", "Each resume section has a stated weight. Points indicate only whether the analyzer found evidence of that section; they do not measure quality.")
    with d:
        card("04 · Matching", "Estimate role alignment", "A weighted local estimate combines recognized skill coverage, section coverage, and contact signals. It is not an employer ATS result or hiring prediction.")
    st.markdown('<div class="section-head"></div>', unsafe_allow_html=True)
    st.info("Text-based PDFs up to 10 MB and 20 pages are supported. Scanned documents need OCR, which is not included. Role matching checks a built-in skill vocabulary and common spelling variants; it may miss synonyms, experience levels, qualifications, or context. The ATS-style estimate uses 70% recognized skill coverage, 20% section coverage, and 10% contact-signal completeness. It is not an employer ATS score or hiring prediction.")
    st.markdown("**Privacy note:** local runs keep analysis in the current Streamlit session and create no resume database or upload archive. On a hosted deployment, the server operator processes the uploaded document; use a deployment you trust.")


with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="brand-mark">✳</div><div><div class="brand-name">RESUMELENS</div><div class="brand-caption">Career intelligence workspace</div></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("<hr>", unsafe_allow_html=True)
    pages = ["Overview", "Resume audit", "Job match", "How it works"]
    prior = st.session_state.get("navigation", "Overview")
    if prior not in pages:
        prior = "Overview"
    current = st.radio("Workspace", pages, index=pages.index(prior), label_visibility="collapsed")
    st.session_state["navigation"] = current
    st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
    st.markdown(
        '<div class="privacy"><b>LOCAL BY DEFAULT</b><br>Resume text is analyzed in memory. No account, tracking database, or external AI service is required.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.caption("A practical checklist for your own review. Not legal, hiring, or ATS advice.")


if current == "Overview":
    overview_page()
elif current == "Resume audit":
    audit_page()
elif current == "Job match":
    match_page()
else:
    method_page()
