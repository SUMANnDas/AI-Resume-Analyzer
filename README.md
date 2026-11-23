# ResumeLens

ResumeLens is a local-first resume review and job-description comparison app. It extracts selectable text from a PDF, checks for common resume sections, identifies skills from a built-in vocabulary, and shows exact skill overlap with a target role.

The interface is built with Streamlit. PDF extraction uses `pdfminer.six`, and the section and job-match checks are transparent Python rules. There is no account system, database, external AI service, or API key to configure.

## What it does

- **Resume audit:** section coverage checklist, contact-presence signals, detected skills, broad skill clusters, and prioritized suggestions.
- **Achievement review:** transparent checks for action-led lines, numbers in recognizable achievement lines, long lines, first-person wording, and limited text extraction.
- **Job match:** compare recognized skills in a resume with skills found in a pasted job description, with matched and not-detected terms.
- **Privacy-safe exports:** download the resume audit or role comparison as JSON without resume text, job-description text, or personal contact values.
- **Private by default:** documents are analyzed in memory and are not written to an upload folder or database.
- **Local interface:** Streamlit binds to `127.0.0.1` by default.

The score is a section-presence checklist, not a measure of writing quality, ATS compatibility, qualification, or hiring likelihood. Achievement checks use extracted PDF line breaks and a small action-verb and number pattern list; they can miss evidence or misread unusual layouts. Job matching uses exact vocabulary overlap and may miss synonyms or context. Scanned image PDFs are not supported because OCR is not included.

## Requirements

- Windows, macOS, or Linux
- Python 3.11 or newer
- Internet access to install Python packages

## Setup on Windows PowerShell

Open PowerShell in the repository folder and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r App\requirements.txt
```

If PowerShell prevents environment activation, allow it for this terminal session and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Start the app

From the repository root:

```powershell
python -m streamlit run App\App.py
```

Open the local address printed in the terminal, normally <http://127.0.0.1:8501>. Stop the server with `Ctrl+C` in that terminal.

To use the existing project environment instead of creating a new one:

```powershell
.\.venvapp\Scripts\python.exe -m streamlit run App\App.py
```

## Setup on macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r App/requirements.txt
python -m streamlit run App/App.py
```

## Use the workspace

1. Open **Resume audit** and upload a text-based PDF (up to 10 MB and 20 pages).
2. Review section coverage, writing signals, detected skills, contact-presence signals, and prioritized suggestions.
3. Open **Job match**, paste a job description, and compare recognized skills.
4. Download the privacy-safe JSON audit if you want to keep the checklist.

The resume and pasted description remain in the active Streamlit session. Refresh the page or clear the upload to remove the current analysis. A hosted deployment processes the document on its server, so use a host you trust.

## Project layout

```text
App/
  App.py                  Streamlit interface and navigation
  resume_parser_local.py  In-memory PDF extraction and transparent rule-based analysis
  requirements.txt        Runtime dependencies
.streamlit/
  config.toml             Local-only server and privacy settings
```

No database setup is required. Uploaded files are not retained by the new analysis flow.


