import time
import requests
import json
import base64
from typing import Dict, Any

from config import GROQ_API_KEY

def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def extract_receipt_data(image_path: str) -> Dict[str, Any]:
    """
    Sends an image path to Groq Vision API (Llama 3.2 90B) to extract structured receipt data.
    Includes validation and robust error handling.
    """
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    encoded_image = encode_image(image_path)

    # UPDATED PROMPT: Specific OCR instructions + German/English support + Strict JSON
    prompt_text = """
    You are an OCR extraction engine.
    Extract EXACT values from the receipt image OR bank transaction screenshot.

    Rules:
    - Do not guess missing numbers.
    - If unreadable, use null.
    - German and English receipts are possible.
    - Decimal separator may be comma or dot.
    - Convert decimal comma to dot.
    - Currency must be ISO format (EUR, USD).
    - Output STRICT JSON only. No markdown.
    
    Specific for Bank Screenshots (e.g. Sparkasse):
    - Map "Receiver" or "Empfänger" to 'vendor'.
    - Map "Amount" or "Betrag" to 'total'.
    - Map "Date" or "Buchungstag" to 'date'.

    Keys:
    date (YYYY-MM-DD)
    vendor
    total (number)
    currency (ISO)
    category
    items (array of strings)

    If a field is missing, use null.
    """

    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": prompt_text
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded_image}"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.1,
        "max_tokens": 1024,
        "top_p": 1,
        "stream": False,
        "stop": None
    }

    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        content = data['choices'][0]['message']['content']
        
        # Robust JSON extraction using Regex
        # The model might return ```json or just ``` or extra text.
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        
        if json_match:
            parsed_data = json.loads(json_match.group(0))
        else:
            # Fallback if no JSON structure found, try raw parse
            parsed_data = json.loads(content)

        # VALIDATION STEP
        if parsed_data.get("total") is not None:
            if isinstance(parsed_data["total"], (int, float)):
                 if parsed_data["total"] < 0:
                    print("Validation Error: Total is negative.")
                    # Optional: handle or return partial data
            else:
                print("Validation Error: Total is not a number.")
        
        # Simple date validation (optional, can be improved)
        if parsed_data.get("date"):
            try:
                # Check if strictly YYYY-MM-DD
                time.strptime(parsed_data["date"], "%Y-%m-%d")
            except ValueError:
                print(f"Validation Warning: Invalid date format {parsed_data['date']}")
                # Attempt to fix or set to None? For now just log.

        return parsed_data
        
    except json.JSONDecodeError:
        print(f"Invalid JSON returned from LLM: {content}")
        return {}
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        try:
            print(f"Response Body: {e.response.text}")
        except:
            pass
        return {}
    except Exception as e:
        print(f"Error extracting data from Groq: {e}")
        return {}
