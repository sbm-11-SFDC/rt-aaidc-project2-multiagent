# 📚 Multi-Agent Publication Reviewer & Recommendation System 
(AAIDC — Module 2 / Production-Ready Version — Module 3)

This repository contains a production-ready multi-agent AI system that analyzes GitHub repositories, evaluates the quality of their documentation, and produces structured improvement recommendations.

The system demonstrates agent collaboration, human-in-the-loop supervision, automated reasoning, safety enhancements, UI-based interaction, and traceable execution — aligned with industry expectations for real-world AI applications.

Originally built for Module 2 of the Ready Tensor Agentic AI Developer Certification, this upgraded version integrates Module 3 requirements by adding a resilient workflow, a Streamlit interface, comprehensive testing, improved error handling, and enhanced observability.

## 🌟 What the System Does

Rather than acting as a simple text analyzer, this system conducts a reviewer-style assessment of a repository’s README file. Multiple specialist agents evaluate structure, keyword usage, clarity, missing documentation signals, thematic representation, and content quality. Outputs are consolidated into a final report that can be used to improve open-source repositories or internal documentation standards.

The application retrieves repository content, examines it through coordinated agent reasoning steps, invites human validation where needed, and presents the synthesized output as actionable recommendations.

## 🧩 Multi-Agent Architecture

The assistant consists of four collaborating agents, each specializing in a different role:

1. Repository Analyzer — inspects README structure, word density, and missing sections.

2. Tag Recommender — extracts semantic signals and proposes meaningful tags via lightweight keyword analysis.

3. Content Improver — rewrites titles and introductory paragraphs to improve clarity and structure.

4. Reviewer — aggregates agent outputs into a refined report suitable for publication or review submission.

Human insight is layered in between to resolve ambiguity, correct context, and override suggestions where needed.

## 🖥 New User Interface (Module 3 Upgrade)

To make the system accessible beyond CLI usage, a full Streamlit UI has been added:

✔ Form-based repo submission

✔ Optional reviewer notes (HITL input)

✔ Real-time execution feedback

✔ Side-by-side display of recommendations and keywords

✔ Built-in validation and error messaging

Run the app:
streamlit run ui/app.py

## 🔐 System Safety, Reliability & Error Handling

The Module 3 version introduces defensive engineering practices:

Retry logic with backoff for network failures

Input validation and sanitization for repository URLs and content

Graceful fallback responses for empty or malformed READMEs

Logging for debugging and traceability

Human approval checkpoints before critical transitions

Together, these mechanisms demonstrate resilience and transparency — key expectations when shipping production-grade AI systems.

🧪 Testing & Quality Assurance

A complete pytest test suite is included:

✔ URL validation
✔ Keyword extraction logic
✔ Workflow execution test using monkeypatching
✔ Assertions on HITL propagation into final recommendations

Run all tests:

python -m pytest

All tests finish successfully, validating workflow correctness and HITL integration.

## 🌟 Key Features

This system goes beyond a simple text analyzer by enabling cooperation between multiple agents, each responsible for a distinct aspect of the review pipeline.
Every agent contributes unique insights, and the orchestrator ensures that the sequence of analysis is deterministic, explainable, and robust.

The workflow includes:

Automated retrieval of README content from GitHub

Keyword extraction and tag recommendation

Content enhancement suggestions (title, intro, missing sections)

Final reviewer report combining all agent outputs

Human-in-the-loop checkpoints allowing the user to approve or edit intermediate results

Error handling to safely recover from malformed URLs, missing READMEs, or API failures

Clear logging and output persistence to the outputs/ directory


## 🧩 System Architecture
Agents & Their Roles
| Agent                      | Purpose                                             |
| -------------------------- | --------------------------------------------------- |
| **Repo Analyzer Agent**    | Reads GitHub repo, extracts README + file structure |
| **Tag Recommender Agent**  | Extracts keywords and proposes project tags         |
| **Content Improver Agent** | Suggests better title/summary and missing sections  |
| **Reviewer Agent**         | Consolidates all findings into final report         |

## 🛠 Tools Used
Several tools extend the intelligence of the agents:
| Tool                               | Purpose                                                              |
| ---------------------------------- | -------------------------------------------------------------------- |
| **GitHub Content Reader**          | Fetches README content using GitHub’s raw content and API patterns.  |
| **YAKE Keyword Extractor**         | Identifies salient keywords for tag generation.                      |
| **Google Gemini LLM**              | Generates improved summaries, titles, and the final reviewer report. |
| **Tenacity-based retry mechanism** | Ensures resilience against transient network failures.               |

## 🧰 Tech Stack
| Component          | Technology    |
| ------------------ | ------------- |
| Language           | Python 3.9+   |
| Framework          | LangGraph     |
| LLM                | Google Gemini |
| Keyword Extraction | YAKE          |
| Environment        | dotenv        |
| Output             | Text reports  |

## 📁 Project Structure
![alt text](<Project Structure.png>)

# ⚙️ Installation & Setup

1️⃣ Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

2️⃣ Install dependencies
python -m pip install -r requirements.txt

3️⃣ Configure environment variables
Create a .env file in the project root:
GOOGLE_API_KEY=your_google_api_key_here
.env is protected via .gitignore and will not be committed.

▶️ Running the Application One-time setup (make src a package)

ni .\src\__init__.py -ItemType File -ErrorAction SilentlyContinue

▶️ Running the system (interactive HITL)

Analyze a public GitHub repo with human-in-the-loop checkpoints:

python -m src.app --repo "https://api.github.com/repos/{owner}/{repo}/readme"

💡 Explanation:

{owner} = GitHub username or organization

{repo} = Repository name

This URL correctly points to the GitHub REST API endpoint for the README file.

Example:

python -m src.app --repo "https://github.com/sbm-11-SFDC/rt-aaidc-project2-multiagent"

Non-interactive (automated) mode:

python -m src.app --repo "https://api.github.com/repos/{owner}/{repo}/readme" --no-interactive

Example:

python -m src.app --repo "https://github.com/sbm-11-SFDC/rt-aaidc-project2-multiagent" --no-interactive

UI Mode (recommended for Module 3)
streamlit run ui/app.py

The UI provides guided input, validation, execution trace, and side-by-side results.

Generated reports are saved to:

outputs/recommendations_<timestamp>.txt

outputs/report_<timestamp>.txt

# 🧩 Human-in-the-Loop (HITL) Interaction

At key phases, the system pauses and asks the user:

Proceed? (yes/no/edit)

Edit suggested title / intro / excerpt?

Override auto-generated suggestions?

This ensures trust, transparency, and human oversight—important principles for agentic AI systems.

# 🛡 Production-Grade Enhancements (Module 3 Requirements Achieved)

This repository demonstrates:

✔ UI layer

✔ Logging and observability

✔ Retry + error handling

✔ Validation and sanitization

✔ End-to-end test coverage

✔ HITL design

✔ Non-interactive automation mode

✔ Persistent output storage

# 🏗️ Architecture Overview

The system follows a clear multi-agent pipeline:

Repo Analyzer reads the GitHub repo, extracts README, project metadata, and structural signals.

Tag Recommender generates keyword-based tags using YAKE and document semantics.

Content Improver rewrites and enhances project descriptions, summaries, and titles.

Reviewer Agent evaluates the combined output and produces the final consolidated report.

Human Reviewer (HITL) optionally refines or approves the final result.

# 🛡️ Safety, Error Handling & System Resilience

The system incorporates multiple layers of defensive design:

GitHub fetch failures gracefully fallback with clear messages

Retry logic mitigates temporary API or network failures

Input sanitization protects agents from malformed README content

Shared state prevents inconsistent transitions or data loss

Missing README or empty content is safely detected early

Human approval required before finalizing key stages

These measures collectively ensure the system remains stable, interpretable, and reliable even during edge-case scenarios.

# 📈 Performance Evaluation

Internal evaluation confirmed:

Stable execution across multiple repositories

Correct agent sequencing

Meaningful keyword extraction

Accurate consolidation into final reports

Successful HITL overrides

Resilience during malformed URL / missing README tests

These findings are reflected in test logs and manual experiments.

# 📄 License
This project is licensed under the MIT License.

See the [LICENSE] file for details

# 👤 Author

Suraj Mahale

AI & Salesforce Developer

GitHub: https://github.com/sbm-11-SFDC

