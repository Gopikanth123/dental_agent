# import json
# from typing import Optional
# from datetime import datetime
# from mcp_server.server import mcp
# from database import DUMMY_PATIENTS, DUMMY_APPOINTMENTS
# from utils import parse_dob, parse_user_date, normalize_time
# import logging

# logger = logging.getLogger("MCP-TOOLS") 

# @mcp.tool()
# def lookup_patient(first_name: Optional[str] = None, last_name: Optional[str] = None) -> str:
#     """
#     Finds a patient by name.
#     """
#     logger.info(f"Looking up patient: first_name={first_name}, last_name={last_name}")
#     matches = []
#     f_query = first_name.lower() if first_name else ""
#     l_query = last_name.lower() if last_name else ""

#     for pid, details in DUMMY_PATIENTS.items():
#         # Fuzzy match: "Rose" matches "Rose Tyler"
#         f_match = not f_query or f_query in details["first_name"].lower()
#         l_match = not l_query or l_query in details["last_name"].lower()
        
#         if f_match and l_match:
#             matches.append({"patient_id": pid, **details})

#     if len(matches) == 1:
#         p = matches[0]
#         return json.dumps({
#             "success": True,
#             "patient_id": p["patient_id"],
#             "patient_name": p["first_name"],
#             "message": "Patient found."
#         })
#     elif len(matches) > 1:
#         return json.dumps({
#             "success": False, 
#             "error": "Multiple patients found. Please ask for Date of Birth."
#         })
        
#     return json.dumps({
#         "success": False, 
#         "error": "No patient found with that name."
#     })

# @mcp.tool()
# def register_patient(first_name: str, last_name: str, dob: str) -> str:
#     """
#     Registers a NEW patient. This should only be called after:
#     - The user says they have NOT been to the office before, OR
#     - lookup_patient failed and the user confirmed creation.

#     DOB is required and must be a valid date.
#     """
#     logger.info(f"Registering new patient: {first_name} {last_name}, DOB={dob}")
#     # Parse and validate DOB
#     parsed_dob = parse_dob(dob)
#     if not parsed_dob:
#         return json.dumps({
#             "success": False,
#             "error": "Invalid date of birth. Please provide DOB in a format like 'April 10 1994'."
#         })

#     # Generate a unique patient ID
#     new_count = len(DUMMY_PATIENTS) + 1
#     new_id = f"pat_{new_count:03d}"

#     # Save to in-memory database
#     DUMMY_PATIENTS[new_id] = {
#         "first_name": first_name,
#         "last_name": last_name,
#         "dob": parsed_dob,
#         "phone": "555-0000",
#         "email": "new.patient@example.com",
#         "appointment_ids": [],
#         "notes": "New patient registration."
#     }

#     return json.dumps({
#         "success": True,
#         "patient_id": new_id,
#         "patient_name": first_name,
#         "message": f"Welcome, {first_name}. I've created a new patient record for you."
#     })

# @mcp.tool()
# def check_availability(date_text: str, time_text: str) -> str:
#     """
#     Checks if a time is valid.
#     FOR DEMO PURPOSES: Always returns TRUE if it's a Weekday 8am-5pm.
#     Ignores existing bookings to ensure 'Happy Path'.
#     """
#     logger.info(f"Checking availability for date='{date_text}', time='{time_text}'")
#     # 1. Parse Date
#     date_val = parse_user_date(date_text)
#     if not date_val:
#         # Fallback swap check (if LLM swapped date/time)
#         date_val = parse_user_date(time_text)
#         if date_val:
#             # Swap variables
#             temp = date_text
#             date_text = time_text
#             time_text = temp
#         else:
#             return json.dumps({"success": False, "error": "I couldn't understand the date. Could you say the day again?"})

#     dt_obj = datetime.strptime(date_val, "%Y-%m-%d")
#     readable_date = dt_obj.strftime("%A, %B %d")

#     # 2. Weekend Check
#     if dt_obj.weekday() >= 5:
#         return json.dumps({"success": False, "error": "We're closed on weekends. How about a weekday?"})

#     # 3. Time Check
#     norm_time = normalize_time(time_text)
#     if not norm_time:
#         # Check if time is in the date string (e.g. "Monday 8am")
#         norm_time = normalize_time(date_text)
    
#     if not norm_time:
#         return json.dumps({"success": False, "error": "I didn't catch the time. Could you repeat it?"})

#     hour = int(norm_time.split(":")[0])
    
#     # 4. Business Hours (8am - 5pm)
#     if hour < 8 or hour >= 17:
#         return json.dumps({"success": False, "error": "We're open 8:00 a.m. to 5:00 p.m."})

#     # 5. SUCCESS (Collision check removed for Demo Stability)
#     return json.dumps({
#         "success": True,
#         "date": date_val,
#         "time": norm_time,
#         "readable_date": readable_date,
#         "message": f"Yes, {readable_date} at {time_text} is available!"
#     })

# @mcp.tool()
# def schedule_appointment(patient_id: str, date_text: str, time_text: str, reason: str = "Check-up") -> str:
#     """Books the appointment."""
#     logger.info(f"Scheduling appointment for patient_id={patient_id}, date='{date_text}', time='{time_text}', reason='{reason}'")
#     # Re-parse to be safe
#     date_val = parse_user_date(date_text)
#     if not date_val: date_val = parse_user_date(time_text) # Swap fallback

#     norm_time = normalize_time(time_text)
#     if not norm_time: norm_time = normalize_time(date_text) # Swap fallback

#     if not date_val or not norm_time:
#         return json.dumps({"success": False, "error": "Invalid parameters."})

#     new_id = f"apt_{len(DUMMY_APPOINTMENTS) + 1001}"
    
#     DUMMY_APPOINTMENTS[new_id] = {
#         "patient_id": patient_id,
#         "date": date_val,
#         "time": norm_time,
#         "status": "confirmed"
#     }

#     return json.dumps({
#         "success": True,
#         "appointment_id": new_id,
#         "message": "Appointment confirmed."
#     })

import json
from typing import Optional
from datetime import datetime
from mcp_server.server import mcp
from database import DUMMY_PATIENTS, DUMMY_APPOINTMENTS, DUMMY_DOCTORS
from utils import parse_dob, parse_user_date, normalize_time
import logging

logger = logging.getLogger("MCP-TOOLS")

@mcp.tool()
def get_doctor_info() -> str:
    """
    Returns a simplified list of available doctors and their services.
    Used by the agent to validate medical needs and assign the correct specialist.
    """
    logger.info("Fetching doctor information (projected view).")
    
    # PROJECTING DATA:
    # We only return what the LLM needs (Name + Services) to keep context clean
    # and avoid exposing internal IDs or private fields.
    projected_doctors = []
    for doc in DUMMY_DOCTORS.values():
        projected_doctors.append({
            "name": doc["name"],
            "specialization": doc["specialization"],
            "services": doc["services"]
        })

    return json.dumps({
        "doctors": projected_doctors,
        "success": True
    })

@mcp.tool()
def lookup_patient(first_name: Optional[str] = None, last_name: Optional[str] = None) -> str:
    """
    Finds a patient by name.
    """
    logger.info(f"Looking up patient: first_name={first_name}, last_name={last_name}")
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
    logger.info(f"Registering new patient: {first_name} {last_name}, DOB={dob}")
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
    logger.info(f"Checking availability for date='{date_text}', time='{time_text}'")
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

    # 5. SUCCESS
    return json.dumps({
        "success": True,
        "date": date_val,
        "time": norm_time,
        "readable_date": readable_date,
        "message": f"Yes, {readable_date} at {time_text} is available!"
    })

@mcp.tool()
def schedule_appointment(
    patient_id: str, 
    date_text: str, 
    time_text: str, 
    reason: str, 
    doctor_name: str
) -> str:
    """
    Books the appointment.
    REQUIRES 'doctor_name' and 'reason'.
    VALIDATES that the provided doctor_name exists in the system.
    """
    logger.info(f"Scheduling: pat={patient_id}, doc='{doctor_name}', reason='{reason}'")
    
    # --- 1. Validate Doctor Existence (Production Safety) ---
    # Create a lookup map (lowercase -> real name)
    valid_doctors_map = {doc["name"].lower(): doc["name"] for doc in DUMMY_DOCTORS.values()}
    
    input_name_clean = doctor_name.strip()
    matched_doctor_name = None

    # Check A: Exact match (case insensitive)
    if input_name_clean.lower() in valid_doctors_map:
        matched_doctor_name = valid_doctors_map[input_name_clean.lower()]
    else:
        # Check B: Partial match (e.g. "Dr. Carter" matches "Dr. Emily Carter")
        for full_name in valid_doctors_map.values():
            if input_name_clean.lower() in full_name.lower():
                matched_doctor_name = full_name
                break
    
    if not matched_doctor_name:
        # Return error if the agent hallucinated a name or user gave an invalid one
        return json.dumps({
            "success": False,
            "error": f"Doctor '{doctor_name}' is not recognized. Available doctors: {', '.join(valid_doctors_map.values())}."
        })

    # --- 2. Validate Date/Time ---
    date_val = parse_user_date(date_text)
    if not date_val: date_val = parse_user_date(time_text)

    norm_time = normalize_time(time_text)
    if not norm_time: norm_time = normalize_time(date_text)

    if not date_val or not norm_time:
        return json.dumps({"success": False, "error": "Invalid date or time parameters."})

    # --- 3. Book Appointment ---
    new_id = f"apt_{len(DUMMY_APPOINTMENTS) + 1001}"
    
    DUMMY_APPOINTMENTS[new_id] = {
        "patient_id": patient_id,
        "doctor_name": matched_doctor_name, # Store the canonical name
        "date": date_val,
        "time": norm_time,
        "reason": reason,
        "status": "confirmed"
    }

    return json.dumps({
        "success": True,
        "appointment_id": new_id,
        "message": f"Appointment confirmed with {matched_doctor_name}."
    })