# DataForge Pioneers: AI Data Analyzer

> Upload a CSV, ask questions in plain English, and get answers with interactive charts. No code required.

DataForge Pioneers is an AI-powered analytics dashboard. You upload a dataset and chat with **DataForger**, an AI data scientist powered by Google Gemini. For every question it writes a factual answer, generates an interactive Plotly chart, and often adds a bonus insight with a second chart for comparison.

## Features

- **Chat with your data:** ask questions about any CSV in natural language.
- **Factual answers:** responses state the actual conclusion from the data (for example, which category had the highest revenue), not just a description of what a chart shows.
- **Interactive Plotly charts:** the AI generates pandas and Plotly code, which the backend runs and returns as JSON for the browser to render.
- **Bonus insight and comparison graph:** each answer can include an extra finding with its own second chart.
- **Self-correcting chart generation:** if the generated chart code fails, the error is sent back to Gemini for one automatic retry.
- **Robust CSV handling:** falls back to `latin1` encoding when UTF-8 fails, and strips HTML wrappers (such as Safari web archive downloads) from uploaded files.
- **Dark-themed visuals** using the `plotly_dark` template.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend / web server | Node.js, Express, EJS, Multer, Axios |
| AI backend | Python, FastAPI, Uvicorn |
| Data and charts | pandas, Plotly |
| LLM | Google Gemini (`google-generativeai`) |

## How It Works

```
Browser  ->  Node.js / Express (port 3000)  ->  FastAPI (/analyze)  ->  Gemini
   ^                                                  |
   +---------- text + Plotly JSON <-------------------+
```

1. The Express server serves the dashboard and receives the uploaded CSV, saving it to `uploads/dataset.csv`.
2. When you ask a question, the request goes to the FastAPI `/analyze` endpoint.
3. FastAPI loads the CSV with pandas and sends Gemini the column types, up to 5,000 rows of data, and your question.
4. Gemini returns strict JSON with four fields: `primary_text`, `primary_graph_code`, `bonus_text`, and `bonus_graph_code`.
5. The backend runs the graph code to build a Plotly figure, retrying once with the error message if it fails.
6. The answer text and chart JSON are returned to the browser and displayed in the chat.

## Project Structure

```
.
├── server.js            # Express server (frontend, uploads)
├── main.py              # FastAPI backend and Gemini integration
├── views/               # EJS templates
├── public/              # Static assets
├── uploads/             # Uploaded datasets
├── package.json         # Node dependencies
└── requirements.txt     # Python dependencies
```

## Prerequisites

- Node.js
- Python 3.9+
- A Google Gemini API key ([get one here](https://aistudio.google.com/app/apikey))

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/KVaman333/DataForge-Pioneers-Analyst-.git
cd DataForge-Pioneers-Analyst-
```

### 2. Frontend (Node.js)

```bash
npm install
```

### 3. Backend (Python)

**Windows**

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Mac / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Add your API key

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_api_key_here
```

The backend will refuse to start if this key is missing. Never commit your `.env` file.

## Running the App

Use two terminals.

1. **Start the frontend** (first terminal):
   ```bash
   npm start
   ```
2. **Start the backend** (second terminal, with the virtual environment activated):
   ```bash
   uvicorn main:app --reload
   ```
3. Open **http://localhost:3000** in your browser, upload a CSV with the paperclip icon, and start asking questions.

## Example Questions

- "Which category generated the highest total revenue?"
- "Show the average price by brand."
- "Compare sales across regions and show the trend over time."

## Known Limitations

- Only the first 5,000 rows of a dataset are sent to the model, so answers on larger files are based on a sample.
- The AI-generated chart code is executed on the server without sandboxing. Run this project locally with datasets you trust, and do not expose it publicly as-is.
- The backend allows requests from any origin (`allow_origins=["*"]`), which is convenient for development but should be restricted in production.
- The app analyzes one dataset at a time (`uploads/dataset.csv`).

## Future Improvements

- Sandbox execution of generated code
- Support for larger datasets through chunking or SQL-style aggregation
- Multi-file and multi-user support
- Export charts and insights as a report

## Author

**Kunal Vaman Dwivedi**
[GitHub](https://github.com/KVaman333) · [LinkedIn](https://linkedin.com/in/kunal-vaman-285200436)
