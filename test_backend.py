import requests

BASE_URL = "http://localhost:5000"

print("Testing save_user...")
user_data = {
    "sign_in_id": "student115",
    "password": "testpass"
}
response = requests.post(f"{BASE_URL}/save_user", json=user_data)
print(response.json())

print("\nTesting get_user...")
response = requests.get(f"{BASE_URL}/get_user/student115")
print(response.json())

print("\nTesting save_backlog_form...")
form_data = {
    "sign_in_id": "student115",
    "dorm": "McMillan",
    "room_number": "214",
    "present": True,
    "completion_date": "2026-03-10",
    "bed_frame": "good",
    "mattress": "bad",
    "carpet": "medium",
    "desk": "good",
    "desk_chair": "terrible_missing",
    "closet_wardrobe": "good",
    "mirror": "medium",
    "room_lighting": "bad",
    "description": "Chair missing and carpet stained.",
    "completion_percentage": 70,
    "form_status": "draft"
}
response = requests.post(f"{BASE_URL}/save_backlog_form", json=form_data)
print(response.json())

print("\nTesting get_backlog_form...")
response = requests.get(f"{BASE_URL}/get_backlog_form/student123")
print(response.json())