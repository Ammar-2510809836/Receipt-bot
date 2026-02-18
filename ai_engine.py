import time
import requests
import json
import base64
from typing import List, Dict, Any

import logging
from config import GROQ_API_KEY

def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def extract_receipt_data(image_path: str) -> List[Dict[str, Any]]:
    """
    Sends an image path to Groq Vision API to extract structured receipt data.
    Returns a LIST of dictionaries (to handle multiple transactions in one screenshot).
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
    
    If there are multiple transactions, output a JSON ARRAY of objects.

    Rules:
    - Do not guess missing numbers.
    - If unreadable, use null.
    - German and English receipts are possible.
    - Decimal separator may be comma or dot.
    - Convert decimal comma to dot.
    - Currency must be ISO format (EUR, USD).
    - Output STRICT JSON only. No markdown.
    - IGNORE lines that are balances/headers (e.g., "Guthaben", "Balance", "Kontostand", "Information").
    - ONLY extract valid transactions with a specific nonzero amount.
    
    Specific for Bank Screenshots (e.g. Sparkasse):
    - Map "Receiver" or "Empfänger" to 'vendor'.
    - Map "Amount" or "Betrag" to 'total'.
    - Map "Date" or "Buchungstag" to 'date'.
    - Ignore "Guthaben auf Girokonten" or similar balance summaries.

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

    # Retry Loop for Robustness
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data['choices'][0]['message']['content']
            
            # Robust JSON extraction using Regex
            import re
            # Try to find list first, then object
            json_match = re.search(r'\[.*\]', content, re.DOTALL) or re.search(r'\{.*\}', content, re.DOTALL)
            
            parsed_data = []

            if json_match:
                raw_json = json.loads(json_match.group(0))
            else:
                # Fallback if no JSON structure found, try raw parse
                raw_json = json.loads(content)
            
            # Normalize to list
            if isinstance(raw_json, list):
                parsed_data = raw_json
            elif isinstance(raw_json, dict):
                parsed_data = [raw_json]
            else:
                logging.error("JSON is neither dict nor list")
                continue

            # VALIDATION STEP (Iterate through items)
            valid_items = []
            for item in parsed_data:
                # 1. Filter out Balance/Header rows by Vendor Name
                vendor_name = str(item.get('vendor', '')).lower()
                if any(x in vendor_name for x in ['guthaben', 'balance', 'kontostand', 'information']):
                    logging.info(f"Skipping balance row: {vendor_name}")
                    continue

                # 2. Basic Total Validation
                if item.get("total") is not None:
                    if isinstance(item["total"], (int, float)):
                        # Bank transactions are often negative. Convert to positive for expense tracking.
                        val = abs(item["total"])
                        
                        # Filter out zero amounts (headers often have 0.0 or null)
                        if val == 0:
                            logging.info(f"Skipping zero amount item: {item}")
                            continue
                            
                        item["total"] = val
                    else:
                        logging.warning(f"Validation Error: Total is not a number in item {item}")
                        continue # Skip invalid item

                # Date Validation
                if item.get("date"):
                    try:
                        time.strptime(item["date"], "%Y-%m-%d")
                    except ValueError:
                        logging.warning(f"Validation Warning: Invalid date format {item.get('date')}")
                
                valid_items.append(item)

            return valid_items
            
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP Error (Attempt {attempt+1}/{max_retries}): {e}")
            try:
                logging.error(f"Response Body: {e.response.text}")
            except:
                pass
            
            if e.response.status_code >= 500:
                time.sleep(2)
                continue
            else:
                return [] 
                
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON returned from LLM: {content}")
            return []
        except Exception as e:
            logging.error(f"Error extracting data from Groq: {e}")
            return []
    
    return []
