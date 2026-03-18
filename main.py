import os
import json
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
from dotenv import load_dotenv
import re

# ==========================================
# 1. AI CONFIGURATION (Secure via .env)
# ==========================================
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("API Key missing! Please add GEMINI_API_KEY to your .env file.")

genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model. Using a try-except to handle older versions of the SDK
try:
    model = genai.GenerativeModel(
        'gemini-3-flash-preview', 
        generation_config={"response_mime_type": "application/json"}
    )
except Exception:
    model = genai.GenerativeModel('gemini-pro')

# ==========================================
# 2. SERVER SETUP
# ==========================================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def execute_graph_code(code_str, df):
    """Safely executes the AI's python code and extracts the Plotly JSON."""
    if not code_str or code_str.strip() == "":
        return None
    
    local_vars = {'pd': pd, 'px': px, 'go': go, 'df': df}
    exec(code_str, {}, local_vars)
    
    fig = local_vars.get('fig')
    if fig:
        return fig.to_json()
    return None

def clean_json_response(text):
    """Strips Markdown formatting if the AI accidentally includes it."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def clean_uploaded_file(filepath):
    """Removes Safari Web Archive or HTML wrappers from uploaded CSVs."""
    try:
        with open(filepath, 'rb') as f:
            raw_data = f.read()
            
        text = raw_data.decode('utf-8', errors='ignore')
        
        if '<pre' in text.lower():
            match = re.search(r'<pre[^>]*>(.*?)</pre>', text, re.DOTALL | re.IGNORECASE)
            if match:
                clean_text = match.group(1).strip()
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(clean_text)
    except Exception:
        pass 

# ==========================================
# 4. THE MAIN ANALYZER ROUTE
# ==========================================
@app.post("/analyze")
async def analyze_data(request: ChatRequest):
    dataset_path = "uploads/dataset.csv"
    
    if not os.path.exists(dataset_path):
        return {"primary_text": "I can't seem to find the data. Could you please upload a CSV file using the paperclip icon first?"}

    clean_uploaded_file(dataset_path)

    try:
        try:
            df = pd.read_csv(dataset_path)
        except UnicodeDecodeError:
            df = pd.read_csv(dataset_path, encoding='latin1')
        
        # 1. Extract context
        data_types = df.dtypes.astype(str).to_dict()
        
        # 2. THE SECRET SAUCE: Give the AI the actual data so it can read it!
        # We pass up to 5000 rows as a CSV string. Gemini reads this instantly.
        data_sample = df.head(5000).to_csv(index=False)

        # 3. The Master Prompt
        system_prompt = f"""
        You are 'DataForger', the backend AI engine for the 'DataForge Pioneers' dashboard.
        
        Here is the structure of the uploaded dataset: {data_types}
        
        Here is the actual raw data (sample of up to 5000 rows):
        {data_sample}

        The user is asking: "{request.query}"

        You MUST return a strict JSON object with exactly these 4 keys:
        "primary_text": A professional text response answering their query. IMPORTANT: Because you can read the raw data above, you MUST explicitly state the factual conclusion/answer in your text (e.g., "Based on the data, the 3 Series generated the highest total revenue...", or "The average price is X...").
        "primary_graph_code": Python code using pandas (as 'df') and plotly.express (as 'px'). 
                              You must save the final graph to a variable named 'fig'. 
                              Use df.dropna() on relevant columns before plotting.
                              If no graph is needed, make this an empty string "".
        "bonus_text": An optional extra insight with its own explicit, factual conclusion (leave empty string if none).
        "bonus_graph_code": Optional python code for a second graph (leave empty string if none).

        CODE RULES:
        - Return ONLY the raw JSON object. NO Markdown wrappers like ```json.
        - Output raw python code inside the JSON string for the graph. 
        - The dataframe is already loaded in memory as 'df'.
        - Do not use fig.show(). Just define the 'fig' variable.
        - Use dark-themed styling if possible (template='plotly_dark').
        """

        # --- STRIKE 1: Initial Attempt ---
        response = model.generate_content(system_prompt)
        clean_text = clean_json_response(response.text)
        ai_data = json.loads(clean_text)

        primary_graph_json = None
        if ai_data.get("primary_graph_code"):
            try:
                primary_graph_json = execute_graph_code(ai_data["primary_graph_code"], df)
            except Exception as e:
                
                # --- STRIKE 2: The Error Correction Loop ---
                error_prompt = system_prompt + f"\n\nCRITICAL ERROR: Your previous code failed to execute with this error: {str(e)}. Please fix the Python code and return the JSON object again."
                response2 = model.generate_content(error_prompt)
                clean_text2 = clean_json_response(response2.text)
                ai_data = json.loads(clean_text2)
                
                try:
                    primary_graph_json = execute_graph_code(ai_data["primary_graph_code"], df)
                except Exception as e2:
                    return {
                        "primary_text": f"I analyzed the data and found that: {ai_data.get('primary_text')}. However, I ran into a formatting issue when trying to draw the graph.",
                        "primary_graph_json": None
                    }

        bonus_graph_json = None
        if ai_data.get("bonus_graph_code"):
            try:
                bonus_graph_json = execute_graph_code(ai_data["bonus_graph_code"], df)
            except:
                pass

        return {
            "primary_text": ai_data.get("primary_text", "Analysis complete."),
            "primary_graph_json": primary_graph_json,
            "bonus_text": ai_data.get("bonus_text", ""),
            "bonus_graph_json": bonus_graph_json
        }

    except Exception as e:
        return {"primary_text": f"A system error occurred: {str(e)}."}