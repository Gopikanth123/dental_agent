from datetime import datetime, timedelta
from typing import Dict, List

# =============================================================================
# 1. PATIENTS DATABASE
# =============================================================================
DUMMY_PATIENTS: Dict[str, dict] = {
    "pat_001": {
        "first_name": "John",
        "last_name": "Doe",
        "dob": "1985-05-20",
        "phone": "555-0101",
        "email": "j.doe@example.com",
        "appointment_ids": ["apt_101", "apt_105"],
        "notes": "Prefers morning appointments. Sensitive teeth."
    },
    "pat_002": {
        "first_name": "Jane",
        "last_name": "Smith",
        "dob": "1992-11-15",
        "phone": "555-0102",
        "email": "jane.s@example.com",
        "appointment_ids": ["apt_102"],
        "notes": "Nervous patient - be extra gentle."
    },
    "pat_003": {
        "first_name": "Michael",
        "last_name": "Chen",
        "dob": "1978-03-10",
        "phone": "555-0103",
        "email": "mike.chen@example.com",
        "appointment_ids": [],
        "notes": "VIP. Usually books for cleaning."
    },
    # --- The Demo Patient (Rose) ---
    "pat_006": {
        "first_name": "Rose",
        "last_name": "Tyler",
        "dob": "1995-04-12",
        "phone": "555-0199",
        "email": "badwolf@example.com",
        "appointment_ids": ["apt_109"], 
        "notes": "Regular. Easy going."
    },
    # --- Duplicate Name Test Cases (John Smith) ---
    "pat_007": {
        "first_name": "John",
        "last_name": "Smith",
        "dob": "1980-01-01", 
        "phone": "555-0200",
        "email": "jsmith80@example.com",
        "appointment_ids": [],
        "notes": "Older John Smith."
    },
    "pat_008": {
        "first_name": "John",
        "last_name": "Smith",
        "dob": "2005-06-20", 
        "phone": "555-0201",
        "email": "junior.smith@example.com",
        "appointment_ids": [],
        "notes": "Younger John Smith (Student)."
    },
    "pat_009": {
        "first_name": "Emily",
        "last_name": "Blunt",
        "dob": "1983-02-23",
        "phone": "555-0300",
        "email": "emily.b@example.com",
        "appointment_ids": ["apt_110"],
        "notes": "Needs to premedicate before visits."
    }
}

# =============================================================================
# 2. APPOINTMENTS DATABASE
# =============================================================================
DUMMY_APPOINTMENTS: Dict[str, dict] = {
    # Past appointment
    "apt_101": {
        "appointment_id": "apt_101",
        "patient_id": "pat_001",
        "patient_name": "John Doe",
        "date": "2024-01-15",
        "time": "09:00",
        "reason": "Annual Cleaning",
        "status": "completed"
    },
    # Future appointment
    "apt_102": {
        "appointment_id": "apt_102",
        "patient_id": "pat_002",
        "patient_name": "Jane Smith",
        "date": "2025-10-05",
        "time": "14:00",
        "reason": "Cavity Filling",
        "status": "confirmed"
    },
    # Rose's past appointment
    "apt_109": {
        "appointment_id": "apt_109",
        "patient_id": "pat_006",
        "patient_name": "Rose Tyler",
        "date": "2024-12-01",
        "time": "10:00",
        "reason": "Check-up",
        "status": "completed"
    },
     "apt_110": {
        "appointment_id": "apt_110",
        "patient_id": "pat_009",
        "patient_name": "Emily Blunt",
        "date": "2025-11-20",
        "time": "11:00",
        "reason": "Whitening",
        "status": "confirmed"
    }
}


# =============================================================================
# 3. FAQ / KNOWLEDGE BASE
# =============================================================================
DUMMY_FAQ = {
    "hours": "We are open Monday through Friday from 8:00 a.m. to 5:00 p.m. We are closed on weekends.",
    "location": "We are located at 123 Smile Street, Suite 101, right next to the Central Park.",
    "parking": "Yes, we have a free parking lot behind the building.",
    "insurance": "We accept most major insurance plans including Delta, Aetna, and Cigna. We also accept CareCredit.",
    "emergency": "If you are in severe pain, please come in immediately. We keep emergency slots open every day.",
    "cancel": "We ask for 24-hour notice for cancellations, otherwise there is a small fee.",
    "payment": "We accept credit cards, cash, and Apple Pay.",
    "new patient": "New patient exams usually take about an hour and include X-rays and a cleaning.",
    "whitening": "Yes, we offer Zoom! in-office whitening and take-home trays."
}

# Export
__all__ = [
    "DUMMY_PATIENTS",
    "DUMMY_APPOINTMENTS"
]