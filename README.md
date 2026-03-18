# DataForge Pioneers - AI Data Analyzer

## Prerequisites

- Node.js installed
- Python 3.9+ installed

## Setup Instructions

### 1. Frontend Setup (Universal)

Open a terminal in the project folder and run:
\`\`\`bash
npm install
\`\`\`

### 2. Backend Setup (OS Dependent)

Open a second terminal in the project folder to set up the Python environment.

**For Mac/Linux:**
\`\`\`bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
\`\`\`

**For Windows:**
\`\`\`cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
\`\`\`

## How to Run the Servers

1. **Start the Frontend:** In your first terminal, run `npm start`
2. **Start the Backend:** In your activated Python terminal, run `uvicorn main:app --reload`
3. Open your browser and navigate to `http://localhost:3000`
