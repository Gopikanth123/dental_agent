from datetime import datetime, date
import dateparser
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def normalize_time(time_str: str) -> Optional[str]:
    try:
        parsed = datetime.strptime(time_str.strip(), '%I:%M %p') # 9:00 AM
    except ValueError:
        try:
            parsed = datetime.strptime(time_str.strip(), '%I %p') # 9 AM
        except ValueError:
            try:
                parsed = datetime.strptime(time_str.strip(), '%H:%M') # 09:00
            except ValueError:
                return None
    return parsed.strftime('%H:%M')

def parse_user_date(date_string: str) -> Optional[str]:
    if not date_string or not date_string.strip():
        return None
    try:
        # ISO Check
        if '-' in date_string and len(date_string) == 10:
            parsed = datetime.strptime(date_string, "%Y-%m-%d")
            if parsed.date() >= date.today(): return date_string
        
        # Natural Language
        parsed = dateparser.parse(date_string, settings={'PREFER_DATES_FROM': 'future', 'REQUIRE_PARTS': ['day', 'month']})
        if parsed and parsed.date() >= date.today():
            return parsed.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        pass
    return None

def parse_dob(date_string: str) -> Optional[str]:
    """Parses DOB, ensures it's in the past."""
    if not date_string: return None
    try:
        parsed = dateparser.parse(date_string, settings={'PREFER_DATES_FROM': 'past'})
        if parsed and parsed.date() <= date.today():
            return parsed.strftime("%Y-%m-%d")
    except:
        pass
    return None