import json
from typing import Optional
from datetime import datetime
from mcp_server.server import mcp
from database import DUMMY_PATIENTS, DUMMY_APPOINTMENTS
from utils import parse_dob, parse_user_date, normalize_time

@mcp.tool()
def lookup_patient(first_name: Optional[str] = None, last_name: Optional[str] = None) -> str:
    """
    Finds a patient by name.
    """
    matches = []
    f_query = first_name.lower() if first_name else ""
    l_query = last_name.lower() if last_name else ""

    for pid, details in DUMMY_PATIENTS.items():
        # Fuzzy match: "Rose" matches "Rose Tyler"
        f_match = not f_query or f_query in details["first_name"].lower()
        l_match = not l_query or l_query in details["last_name"].lower()
        
        if f_match and l_match:
            matches.append({"patient_id": pid, **details})

    if len(matches) == 1:
        p = matches[0]
        return json.dumps({
            "success": True,
            "patient_id": p["patient_id"],
            "patient_name": p["first_name"],
            "message": "Patient found."
        })
    elif len(matches) > 1:
        return json.dumps({
            "success": False, 
            "error": "Multiple patients found. Please ask for Date of Birth."
        })
        
    return json.dumps({
        "success": False, 
        "error": "No patient found with that name."
    })

@mcp.tool()
def register_patient(first_name: str, last_name: str, dob: str) -> str:
    """
    Registers a NEW patient. This should only be called after:
    - The user says they have NOT been to the office before, OR
    - lookup_patient failed and the user confirmed creation.

    DOB is required and must be a valid date.
    """

    # Parse and validate DOB
    parsed_dob = parse_dob(dob)
    if not parsed_dob:
        return json.dumps({
            "success": False,
            "error": "Invalid date of birth. Please provide DOB in a format like 'April 10 1994'."
        })

    # Generate a unique patient ID
    new_count = len(DUMMY_PATIENTS) + 1
    new_id = f"pat_{new_count:03d}"

    # Save to in-memory database
    DUMMY_PATIENTS[new_id] = {
        "first_name": first_name,
        "last_name": last_name,
        "dob": parsed_dob,
        "phone": "555-0000",
        "email": "new.patient@example.com",
        "appointment_ids": [],
        "notes": "New patient registration."
    }

    return json.dumps({
        "success": True,
        "patient_id": new_id,
        "patient_name": first_name,
        "message": f"Welcome, {first_name}. I've created a new patient record for you."
    })

@mcp.tool()
def check_availability(date_text: str, time_text: str) -> str:
    """
    Checks if a time is valid.
    FOR DEMO PURPOSES: Always returns TRUE if it's a Weekday 8am-5pm.
    Ignores existing bookings to ensure 'Happy Path'.
    """
    # 1. Parse Date
    date_val = parse_user_date(date_text)
    if not date_val:
        # Fallback swap check (if LLM swapped date/time)
        date_val = parse_user_date(time_text)
        if date_val:
            # Swap variables
            temp = date_text
            date_text = time_text
            time_text = temp
        else:
            return json.dumps({"success": False, "error": "I couldn't understand the date. Could you say the day again?"})

    dt_obj = datetime.strptime(date_val, "%Y-%m-%d")
    readable_date = dt_obj.strftime("%A, %B %d")

    # 2. Weekend Check
    if dt_obj.weekday() >= 5:
        return json.dumps({"success": False, "error": "We're closed on weekends. How about a weekday?"})

    # 3. Time Check
    norm_time = normalize_time(time_text)
    if not norm_time:
        # Check if time is in the date string (e.g. "Monday 8am")
        norm_time = normalize_time(date_text)
    
    if not norm_time:
        return json.dumps({"success": False, "error": "I didn't catch the time. Could you repeat it?"})

    hour = int(norm_time.split(":")[0])
    
    # 4. Business Hours (8am - 5pm)
    if hour < 8 or hour >= 17:
        return json.dumps({"success": False, "error": "We're open 8:00 a.m. to 5:00 p.m."})

    # 5. SUCCESS (Collision check removed for Demo Stability)
    return json.dumps({
        "success": True,
        "date": date_val,
        "time": norm_time,
        "readable_date": readable_date,
        "message": f"Yes, {readable_date} at {time_text} is available!"
    })

@mcp.tool()
def schedule_appointment(patient_id: str, date_text: str, time_text: str, reason: str = "Check-up") -> str:
    """Books the appointment."""
    # Re-parse to be safe
    date_val = parse_user_date(date_text)
    if not date_val: date_val = parse_user_date(time_text) # Swap fallback

    norm_time = normalize_time(time_text)
    if not norm_time: norm_time = normalize_time(date_text) # Swap fallback

    if not date_val or not norm_time:
        return json.dumps({"success": False, "error": "Invalid parameters."})

    new_id = f"apt_{len(DUMMY_APPOINTMENTS) + 1001}"
    
    DUMMY_APPOINTMENTS[new_id] = {
        "patient_id": patient_id,
        "date": date_val,
        "time": norm_time,
        "status": "confirmed"
    }

    return json.dumps({
        "success": True,
        "appointment_id": new_id,
        "message": "Appointment confirmed."
    })