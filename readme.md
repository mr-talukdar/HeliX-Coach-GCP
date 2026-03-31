# 🏋️‍♂️ HeliX Coach: Autonomous Multi-Agent Fitness Orchestrator

**HeliX Coach** is a state-of-the-art, autonomous fitness management system built for the **Gen AI Academy APAC Edition**. It moves beyond static workout tracking by leveraging a multi-agent architecture that perceives user fatigue, manages persistent training blocks in **AlloyDB**, and autonomously executes real-world actions via the **Google Calendar API**.



## 🚀 Core Features

* **Autonomous Orchestration:** Uses a central "Head Coach" agent to delegate tasks to specialized sub-agents (Routine Generator, Readiness Specialist, Schedule Specialist).
* **Dynamic Auto-Regulation:** Calculates a "Readiness Score" to mutate prescribed workouts in real-time. If you're exhausted, HeliX automatically scales your intensity.
* **Persistent State Memory:** Powered by **AlloyDB AI**, the system remembers your long-term goals and training history across every session using the PostgreSQL Python Connector.
* **Actionable Integration:** Not just a chatbot—HeliX reads your live Google Calendar to find free slots and books your training sessions automatically.

## 🛠️ The Tech Stack

* **Framework:** Google Agent Development Kit (ADK)
* **LLM:** Gemini 2.5 Flash (Vertex AI)
* **Database:** AlloyDB for PostgreSQL
* **Deployment:** Google Cloud Run (Containerized via Docker)
* **APIs:** Google Calendar API v3
* **Backend:** FastAPI & Uvicorn

## 📂 Project Structure

```text
HELIX-ORCHESTRATOR/
├── helix_coach/          # Main Agent Logic
│   ├── agent.py          # Orchestrator & Specialist Definitions
│   ├── database.py       # AlloyDB Connection & CRUD Tools
│   └── calendar_tools.py # Google Calendar API Integrations
├── main.py               # Cloud Run Entry Point (FastAPI Wrapper)
├── Procfile              # Cloud Run Startup Command
├── requirements.txt      # Dependency Lockfile
└── README.md             # Project Documentation


🌟 Why HeliX?
Generic fitness apps are rigid and often lead to overtraining or injury. HeliX is the first step toward a truly "Living" coach. By combining the reasoning of Gemini 2.5 Flash with the persistent memory of AlloyDB, it provides a level of personalization previously only available through expensive human coaching.

Developed by Rahul Talukdar for the Gen AI Academy 2026.