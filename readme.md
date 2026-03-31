# 🏋️‍♂️ HeliX Coach: Autonomous Multi-Agent Fitness Orchestrator

**HeliX Coach** is a state-of-the-art, autonomous fitness management system built for the **Gen AI Academy APAC Edition 2026**. Moving beyond static workout tracking, HeliX leverages a sophisticated multi-agent architecture to perceive user fatigue, manage persistent training blocks in **AlloyDB**, and autonomously execute real-world scheduling via the **Google Calendar API**.

##Live at : https://helix-coach-app-252961914897.us-east4.run.app/

## 🚀 Core Features

* **Autonomous Orchestration:** Features a central `leanx_coach` (Orchestrator) that intelligently delegates tasks to specialized sub-agents:
    * **Routine Generator:** Designs long-term strength programming based on user goals.
    * **Readiness Specialist:** Assesses fatigue and sleep data to scale intensity dynamically.
    * **Schedule Specialist:** Manages calendar availability and automated event booking.
* **Dynamic Auto-Regulation:** Calculates a "Readiness Score" to mutate prescribed workouts in real-time. If recovery is low, HeliX automatically triggers deload protocols to prevent injury.
* **Persistent State Memory:** Powered by **AlloyDB AI**, the system maintains a "shared mental context" of user goals and historical training data across sessions using the PostgreSQL Python Connector.
* **Actionable Tool-Use:** More than a chatbot—HeliX interacts directly with the **Google Calendar API** to identify busy blocks and autonomously book training sessions.

## 🛠️ The Tech Stack

* **Framework:** Google Agent Development Kit (ADK)
* **LLM:** Gemini 2.5 Flash (Vertex AI)
* **Database:** AlloyDB for PostgreSQL
* **Deployment:** Google Cloud Run (Serverless/Containerized)
* **Infrastructure:** Python 3.14+, FastAPI, & Uvicorn

---

## 📂 Project Structure

```text
HELIX-ORCHESTRATOR/
├── helix_coach/          # Core Multi-Agent Logic
│   ├── agent.py          # Orchestrator & Specialist Definitions
│   ├── database.py       # AlloyDB Connection & CRUD Tools
│   └── calendar_tools.py # Google Calendar API v3 Integrations
├── main.py               # Cloud Run Entry Point (FastAPI Wrapper)
├── Procfile              # Production Startup Command
├── requirements.txt      # Dependency Lockfile
└── README.md             # Project Documentation
```
## 🌟 Why HeliX?
Traditional fitness applications are rigid, leading to overtraining and plateaus. HeliX represents the first step toward a truly "Living" coach. By synthesizing the advanced reasoning of Gemini 2.5 Flash with the high-performance persistence of AlloyDB, HeliX provides the level of elite, adaptive personalization previously reserved for professional athletes. It doesn't just suggest—it executes.

## Developer Information
Author: Rahul Talukdar

Project: Gen AI Academy APAC Edition 2026

Track: Agent Development / AlloyDB AI
