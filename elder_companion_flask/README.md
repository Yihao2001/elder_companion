# Elder Companion Flask App

A Flask web application for Elder Companion RAG.

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)

## Setup and Installation

Follow these steps to set up and run the application locally:

### 1. Navigate to Project Directory
```bash
cd elder_companion_flask
```

### 2. Create Virtual Environment
```bash
python -m venv venv
```

### 3. Activate Virtual Environment
```bash
source venv/bin/activate
```

### 4. Save Environment Variables
```bash
export DATABASE_URL='postgresql://neondb_owner:npg_RocZpHi5ey8f@ep-mute-violet-a1l6ie92-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
export DATABASE_ENCRYPTION_KEY='mYDncrsm3liEgbXcMqPWbMN/riyOnCnJh26Z9wkE0K0='
export HUGGINGFACE_TOKEN='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'
```

### 5. Install Dependencies
```bash
pip install -r requirements.txt
```

### 6. Run Flask Application
```bash
python -m flask --app app:app --debug run
```

## Quick Start
For convenience, here's the complete setup in one go:
```bash
cd elder_companion_flask

python -m venv venv

source venv/bin/activate  

export DATABASE_URL='postgresql://neondb_owner:npg_RocZpHi5ey8f@ep-mute-violet-a1l6ie92-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
export DATABASE_ENCRYPTION_KEY='mYDncrsm3liEgbXcMqPWbMN/riyOnCnJh26Z9wkE0K0='
export HUGGINGFACE_TOKEN='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'

pip install -r requirements.txt

python -m flask --app app:app --debug run
```
