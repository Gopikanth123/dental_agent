from datetime import datetime, date, timedelta
import dateparser
import logging
import re

logger = logging.getLogger(__name__)

def normalize_time(time_str: str) -> str:
    """
    Parses natural language time to HH:MM format (24-hour).
    Handles: "8am", "8:00 a.m.", "5pm", "14:00".
    """
    if not time_str: return None
    
    # Clean string: remove spaces, dots, lower case
    raw = time_str.lower().strip().replace(".", "").replace(" ", "")
    
    # Fix common transcript typos
    raw = raw.replace("ym", "am").replace("yn", "am").replace("qm", "pm")

    # Regex for H:MM + am/pm
    match = re.match(r"(\d{1,2}):?(\d{2})?(am|pm)?", raw)
    if match:
        h, m, p = match.groups()
        h = int(h)
        m = int(m) if m else 0
        
        if p == "pm" and h != 12: h += 12
        if p == "am" and h == 12: h = 0
        
        return f"{h:02d}:{m:02d}"
    return None

def parse_user_date(date_string: str) -> str:
    """
    Parses natural language dates (e.g., "next Monday", "tomorrow").
    """
    if not date_string: return None
    
    clean_str = date_string.lower().strip()

    # 1. Remove Prepositions/Noise that confuse the parser
    # "On next Monday" -> "next Monday"
    prefixes = ["on ", "the ", "at "]
    for p in prefixes:
        if clean_str.startswith(p):
            clean_str = clean_str[len(p):]

    # 2. Remove common transcript hallucinations
    noise = ["ethereum", "a theorem", "uh", "um"]
    for word in noise:
        clean_str = clean_str.replace(word, "")

    # 3. Strip time if the LLM accidentally sent it (Safety Net)
    # Remove "8am", "8:00", etc.
    clean_str = re.sub(r'\b\d{1,2}(:\d{2})?\s*(am|pm)\b', '', clean_str)

    # 4. Parse
    settings = {
        'PREFER_DATES_FROM': 'future',
        'PREFER_DAY_OF_MONTH': 'first',
        'RELATIVE_BASE': datetime.now()
    }
    
    parsed = dateparser.parse(clean_str, settings=settings)
    
    if parsed:
        # Business Logic: If we are on Monday, and user says "Monday", 
        # Dateparser might return today. We usually mean *next* Monday in a booking context
        # if the time has passed, but let's stick to strict parser result for now 
        # or shift if it's in the past.
        if parsed.date() < date.today():
             parsed = parsed + timedelta(days=7)
        return parsed.strftime("%Y-%m-%d")
        
    return None

def parse_dob(dob_str: str) -> str:
    parsed = dateparser.parse(str(dob_str), settings={'PREFER_DATES_FROM': 'past'})
    if parsed: return parsed.strftime("%Y-%m-%d")

    return None
