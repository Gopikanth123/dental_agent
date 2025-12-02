from datetime import datetime, timedelta

DUMMY_PATIENTS = {
    "pat_001": {"first_name": "John", "last_name": "Doe", "dob": "1985-05-20", "appointment_ids": ["apt_101"]},
    "pat_002": {"first_name": "Jane", "last_name": "Smith", "dob": "1992-11-15", "appointment_ids": ["apt_102"]},
}

DUMMY_APPOINTMENTS = {
    "apt_101": {"appointment_id": "apt_101", "patient_id": "pat_001", "patient_name": "John Doe", "date": "2025-09-10", "time": "10:00", "reason": "Annual Check-up"},
}

DUMMY_AVAILABILITY = {}
start_date = datetime.now()
for i in range(1, 365):
    date_str = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
    slots = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"] if i % 2 == 0 else ["09:30", "10:30", "11:30", "13:30"]
    DUMMY_AVAILABILITY[date_str] = slots

DUMMY_FAQ = {
    "office hours": "We are open Monday to Friday, from 8:30 AM to 5:00 PM.",
    "insurance": "We accept Cigna, Aetna, and Delta Dental.",
}
