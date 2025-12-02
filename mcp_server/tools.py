import json
from typing import Optional
from mcp_server.server import mcp
from database import DUMMY_PATIENTS, DUMMY_APPOINTMENTS, DUMMY_AVAILABILITY, DUMMY_FAQ
from utils import parse_dob, parse_user_date, normalize_time

@mcp.tool()
def lookup_patient(first_name: str, last_name: str, dob: Optional[str] = None) -> str:
    """Finds a patient record. Returns patient_id or error."""
    matches = []
    for pid, details in DUMMY_PATIENTS.items():
        if details["first_name"].lower() == first_name.lower() and details["last_name"].lower() == last_name.lower():
            matches.append({"patient_id": pid, **details})
    
    if not matches:
        return json.dumps({"success": False, "error": "Patient not found."})
    
    if len(matches) > 1:
        if dob:
            for m in matches:
                if m["dob"] == dob:
                    return json.dumps({"success": True, "patient_id": m["patient_id"]})
        return json.dumps({"success": False, "error": "Multiple patients found. Ask for DOB."})

    return json.dumps({"success": True, "patient_id": matches[0]["patient_id"]})

@mcp.tool()
def register_new_patient(first_name: str, last_name: str, dob: str) -> str:
    """Registers a new patient. DOB is required."""
    valid_dob = parse_dob(dob)
    if not valid_dob:
        return json.dumps({"success": False, "error": "Invalid DOB format."})
    
    new_id = f"pat_{len(DUMMY_PATIENTS) + 1:03d}"
    DUMMY_PATIENTS[new_id] = {
        "first_name": first_name, 
        "last_name": last_name, 
        "dob": valid_dob, 
        "appointment_ids": []
    }
    return json.dumps({"success": True, "patient_id": new_id})

@mcp.tool()
def get_patient_appointments(patient_id: str) -> str:
    """Retrieves upcoming appointments for a patient."""
    if patient_id not in DUMMY_PATIENTS:
        return json.dumps({"success": False, "error": "Patient not found."})
        
    apt_ids = DUMMY_PATIENTS[patient_id].get("appointment_ids", [])
    apts = [DUMMY_APPOINTMENTS.get(aid) for aid in apt_ids if aid in DUMMY_APPOINTMENTS]
    return json.dumps({"success": True, "appointments": apts})

@mcp.tool()
def check_availability(date_text: str) -> str:
    """Checks open slots for a natural language date."""
    date_val = parse_user_date(date_text)
    if not date_val:
        return json.dumps({"success": False, "error": "Invalid date."})
    
    slots = DUMMY_AVAILABILITY.get(date_val, [])
    if not slots:
        return json.dumps({"success": False, "error": "No slots available."})
    
    # Convert to readable AM/PM
    readable = []
    for t in sorted(slots):
        h, m = map(int, t.split(":"))
        suffix = "AM" if h < 12 else "PM"
        readable.append(f"{h if h <= 12 else h-12}:{m:02d} {suffix}")
    
    return json.dumps({"success": True, "date": date_val, "available_slots": readable})

@mcp.tool()
def schedule_appointment(patient_id: str, date_text: str, time: str, reason: str) -> str:
    """Schedules appointment. Requires patient_id, date, time, reason."""
    date_val = parse_user_date(date_text)
    norm_time = normalize_time(time)
    
    if not date_val or not norm_time:
        return json.dumps({"success": False, "error": "Invalid date or time."})
    
    # Check if slot exists
    if norm_time not in DUMMY_AVAILABILITY.get(date_val, []):
        return json.dumps({"success": False, "error": "Slot unavailable."})
    
    new_apt_id = f"apt_{len(DUMMY_APPOINTMENTS) + 101}"
    pat = DUMMY_PATIENTS.get(patient_id)
    
    DUMMY_APPOINTMENTS[new_apt_id] = {
        "appointment_id": new_apt_id, 
        "patient_id": patient_id, 
        "patient_name": f"{pat['first_name']} {pat['last_name']}",
        "date": date_val, 
        "time": norm_time, 
        "reason": reason
    }
    DUMMY_PATIENTS[patient_id]["appointment_ids"].append(new_apt_id)
    DUMMY_AVAILABILITY[date_val].remove(norm_time)
    
    return json.dumps({"success": True, "message": f"Booked for {date_val} at {time}."})

@mcp.tool()
def get_faq_answer(topic: str) -> str:
    """Returns FAQ answers."""
    for k, v in DUMMY_FAQ.items():
        if k in topic.lower():
            return json.dumps({"success": True, "answer": v})
    return json.dumps({"success": False, "error": "No info found."})