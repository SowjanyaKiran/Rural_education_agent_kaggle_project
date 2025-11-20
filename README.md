🌾 Rural Education Agent – AI for Low-Bandwidth Learning

A Kaggle Competition Project

📌 Overview

The Rural Education Agent is a multilingual, bandwidth-aware AI system built to support students in rural and low-resource learning environments.
It performs:

Resource Curation – Loads & filters learning materials based on file size, language, and topic.

Summarization – Generates short summaries for each learning resource (mock or real LLM providers).

Personalized Learning Plans – Assigns a week-long study plan based on student profile & bandwidth availability.

Multi-Agent Q&A Support – A Retriever Agent + QA Agent provide topic explanations and examples.

Session Management – Saves and loads student progress for continuity.

Mock Mode (Offline) – Entire project runs offline using mock summarizer & mock QA logic (ideal for Kaggle review).

This project is fully modular, extendable, and runnable inside Jupyter Lab or command prompt.

🏗 System Architecture

rural-ed-agent/
├── data/
│   ├── sample_resources.csv
│   └── sessions/
├── src/
│   ├── ingest_curator.py
│   ├── summarizer.py
│   ├── translation.py
│   ├── planner.py
│   ├── multi_agent.py
│   ├── session_mem.py
│   ├── observability.py
│   └── utils.py
├── notebooks/
│   ├── 00-setup.ipynb
│   ├── 01-ingest.ipynb
│   ├── 02-summarize.ipynb
│   ├── 03-plan.ipynb
│   └── 04-qa-demo.ipynb
├── tests/
│   ├── test_summarizer.py
│   └── test_planner.py
├── demo_combined.py
├── run_real_agents.py
├── requirements.txt
└── README.md

🚀 Features
1. Resource Ingestion

Reads CSV metadata (title, size, language, URL, tags).

Filters based on bandwidth limits.

Samples resources for demo runs.

2. AI Summarization

Supports:

Mock summarizer (offline)

LLM provider mode (OpenAI, Gemini, HF models) – optional upgrade

Summaries help the retrieval agent answer student questions.

3. Personalized Lesson Planner

Creates 7-day study plan using:

Preferred language

Weekly bandwidth budget

Resource sizes

Summary availability

4. Multi-Agent Q&A System

Retriever Agent → finds best resources for each question

QA Agent → generates answer, explanation, examples, practice questions

5. Session Memory

Stores:

Summaries

Weekly plan

Student metadata

Q&A history

Saved in JSON at:

data/sessions/<student_id>.json

6. Fully Offline Demo

Mock logic allows full execution without API keys.

🔧 Installation
1. Clone or copy the repository

git clone <repo_url>
cd rural-ed-agent

2. Install dependencies

pip install -r requirements.txt

▶ How to Run

Option 1: Full pipeline demo (recommended)
python demo_combined.py
Runs:

Ingestion → Summarization → Learning Plan → Q&A → Session Save

Option 2: Real multi-agent demo
python run_real_agents.py

This uses a more structured multi-agent response generator.

Option 3: Jupyter Notebooks (step-by-step)

Open Jupyter Lab:
jupyter lab
Then run in order:

00-setup.ipynb

01-ingest.ipynb

02-summarize.ipynb

03-plan.ipynb

04-qa-demo.ipynb

🧪 Unit Tests

Run tests with:
pytest tests/

🌐 Multilingual Support

Supports:

English (en)

Hindi (hi)

Kannada (kn)

More languages can be added easily in:
src/translation.py

📊 Project Goals (for Kaggle Submission)

This project aims to:

Improve education accessibility in rural areas with limited internet.

Provide personalized and adaptive learning powered by AI.

Enable multilingual learning for Indian students.

Demonstrate multi-agent reasoning in a real-world scenario.

Run fully in offline/mock mode for safe and reproducible evaluation.

📽 Demo Video (required for competition)

Your demo video should show:

Running the setup notebook

Ingesting & summarizing resources

Creating a weekly plan

Performing Q&A

Showing session JSON output

Suggested length: 2–3 minutes.

🌟 Future Enhancements

FAISS-based semantic retrieval

Real LLM summarization (Gemini / GPT / HF summarizers)

Audio explanations for rural areas with low literacy

WhatsApp/IVR-based student interface

More Indian languages

Offline large language models (LLAMA, Mistral 7B Int4)

🤝 Contribution

Feel free to open issues or PRs.
Modular design allows extending:

Agents

Summarizers

Bandwidth models

UI (Streamlit / FastAPI)

🏁 Conclusion

This project demonstrates how AI can:

Personalize learning

Overcome bandwidth limitations

Support multilingual learners

Operate fully offline

Making it an ideal entry for Kaggle’s Education AI competition.
