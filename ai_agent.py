# ai_agent.py
import json
import os
import re
import pandas as pd
from google import genai
from dotenv import load_dotenv

# Initialize variable lookups natively from your hidden local .env file securely
load_dotenv()

# Extract the credential string safely with zero public exposure risk on GitHub
api_token = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_token)

def handle_warehouse_queries(user_query: str, roster_df: pd.DataFrame) -> str:
    """
    Channel 1: Core Data Analyst Engine.
    Answers specific, real-time factual questions about your local database records.
    """
    # Calculate live skill-badge totals from the actual 100-associate dataframe to feed to the AI
    skill_summary = roster_df.drop(columns=["Current_Assignment"]).sum().to_dict()
    
    # Calculate intersecting advanced cross-training statistics dynamically
    picking_and_cubiscan = int(((roster_df["Picking"] == True) & (roster_df["Cubiscan"] == True)).sum())
    stowing_and_receive = int(((roster_df["Stowing"] == True) & (roster_df["Receive"] == True)).sum())
    
    system_prompt = f"""
    You are an expert Operations Data Analyst for a major fulfillment center.
    Answer the user's question about the 100-associate roster clearly, accurately, and concisely.
    
    Use ONLY this live warehouse metrics data context to formulate your answer:
    - Overall Skill Badges Count: {json.dumps(skill_summary)}
    - Associates with BOTH Picking AND Cubiscan training: {picking_and_cubiscan}
    - Associates with BOTH Stowing AND Receive training: {stowing_and_receive}
    
    Respond with plain, polite text. Do not output markdown code blocks, backticks, or any JSON data strings.
    """
    
    try:
        # Directly target gemini-3.8-flash as enforced by the Google framework parameters
        response = client.models.generate_content(
            model="gemini-3.8-flash", 
            contents=user_query, 
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt, 
                temperature=0.1
            )
        )
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Query Processing Error: {str(e)}"

def handle_warehouse_commands(user_command: str, current_targets: dict) -> dict:
    """
    Channel 2: Direct Headcount Dispatch Command Parser.
    Strictly modifies numeric target thresholds based on textual shift directions.
    """
    system_prompt = f"""
    You are an absolute headcount tracking data parser. Your sole job is to modify these current baseline numbers based on the user text command:
    {json.dumps(current_targets)}
    
    Respond ONLY with a valid JSON block containing updated integers for all 10 keys:
    "Cubiscan Picking", "Pallet Stower", "Instructor", "Prep", "Pallet Puller", "Cubiscan", "Cart Builder", "Decant", "Receive", "Picking".
    
    Rules:
    1. If the user says 'Add 5 to Decant', add 5 to the current value of 'Decant'.
    2. If the user says 'Set Picking to 20', change the 'Picking' value to exactly 20.
    
    No other text, explanations, markdown blocks (like ```json), backticks, or wrappers allowed. Output raw JSON only.
    """
    
    try:
        # Direct unified model submission request call pipeline
        response = client.models.generate_content(
            model="gemini-3.8-flash", 
            contents=user_command, 
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt, 
                temperature=0.1
            )
        )
        
        raw_text = response.text.strip()
        
        # Pull matching bracket structures out of the text response stream cleanly
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            updated = json.loads(json_match.group(0))
            # Verify and preserve structural target matrix fields if any are dropped by the AI model
            for key in current_targets.keys():
                if key not in updated: 
                    updated[key] = current_targets[key]
            return updated
            
        return current_targets
    except Exception:
        return current_targets
