# Kestrelford Repairs Decision Lab

A decision-making and learning platform built with Python and Streamlit.

🔗 **Live Demo:** https://pm-decision-lab.streamlit.app/

> **Note:** This is a fictional training scenario created for educational purposes only.

## Features

- **Learner Portal** – Access learning tracks and activities.
- **Interactive Scenarios** – Practise decision-making through branching scenarios.
- **Progress Tracking** – Save and resume learning progress.
- **Scoring System** – Track decisions, outcomes, and performance.
- **Admin Dashboard** – Manage learners, activities, and results.
- **H5P Integration** – Upload, validate, publish, and manage H5P activities.
- **Reports & Analytics** – View learner progress and export reports.
- **PDF Downloads** – Download learner practice records.
- **Database Support** – SQLite for local development and PostgreSQL for deployment.

## Technology Stack

- Python
- Streamlit
- FastAPI
- SQLAlchemy
- SQLite / PostgreSQL
- H5P
- LTI 1.3 and xAPI

## Run Locally

**Requirements:** Python 3.10–3.12 recommended.

```bash
git clone https://github.com/MenukaRanasinghe/PM-Decision-Lab.git
cd PM-Decision-Lab

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
copy .env.example .env

python -m tools.create_admin
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Run Tests

```bash
pytest -q
```

## Disclaimer

This application is designed for educational and training purposes. Kestrelford Repairs is fictional and does not represent a real housing provider or live service.
