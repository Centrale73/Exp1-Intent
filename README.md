

---

# Exp1-Intent

**Intent Governance CLI Demo**
Interactive Python project demonstrating an *intent governance layer* wrapped around an agent for safe execution of customer-support prompts.

---

## 🚀 Overview

This project implements an **Intent Governance Layer** combining multiple safety and evaluation primitives around an agent framework. It enables running natural-language “intents” (like refund requests or support actions) from the terminal with governance rules (e.g., confirmation for sensitive actions and post-run scoring).

---

## 🧠 What It Does

* Starts an interactive CLI for typed intents.
* Wraps an agent with governance rules (constitution + judge criteria).
* Processes and evaluates agent outputs.
* Supports simulated customer support actions (e.g., send emails, refunds).

---

## 📦 Features

* 👉 **Interactive CLI demo** powered by *rich*.
* 🤖 Agent that responds to natural language prompts.
* 🛡 Intent governance layer enforcing safety/ethics criteria.
* ☑ Tool confirmation prompts for sensitive actions.

---

## 📁 Repository Structure

```
├── constitutions/          # YAML definitions for governance rules
├── criteria/               # Judge criteria text files
├── evals/                  # Evaluation logic for scoring responses
├── intent/                 # Intent retrieval logic
├── hooks/                  # Hook functions injected into agent
├── models/                 # Model selection and factory
├── tools/                  # Demo tools (refund, email, etc.)
├── tests/                  # Test suite
├── .env.example            # Environment template
├── main.py                 # Interactive CLI entry point
├── governor.py             # Governance layer implementation
├── requirements.txt        # Project dependencies
└── .gitignore
```

---

## 🛠 Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/Centrale73/Exp1-Intent.git
   cd Exp1-Intent
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   This project uses:

   * `agno`, `pyyaml`, `python-dotenv`, `httpx`, `rich`, `pytest`
   * Large-language-model backends such as `openai`, `anthropic`, `langchain`, `langgraph` ([GitHub][1])

3. **Configuration**

   * Copy `.env.example` to `.env`
   * Add your Perplexity (or similar) API key to `.env`

---

## ▶️ Running the Demo

```bash
python main.py
```

You should see a prompt where you can enter sample intents such as:

```
Refund $500 to customer C-1234  
Send an email to user@example.com  
Cancel the subscription for customer C-5678  
Process a chargeback of $200 for customer C-9012  
```

Type:

```
quit
```

to exit the CLI.

---

## 💡 Example Intents

Once running, try:

```
Refund $200 to customer C-9012  
Send an email to confirm order completion  
Cancel subscription for account ABC123
```

The system will run these through the agent and show outputs along with any governance handling.

---


## 🧩 Business Adaptation Example (Cirkanime)

This repo now includes a concrete adaptation blueprint for an event-based business
(Cirkanime):

- `docs/cirkanime_engine_modifications.md` — recommended engine and agent topology
- `constitutions/cirkanime.yaml` — event/booking governance policy example
- `criteria/cirkanime_voice.txt` — judge criteria for parent-facing communication
- `tools/crm_tools.py` — CRM + booking tool stubs for a creator-operated workflow

## 🧪 Tests

Run the test suite with:

```bash
pytest
```

---

## 📄 License

MIT License

---
