"""Check available resources (rooms, time slots, teachers)."""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def check_resources():
    """Check available resources for scheduling."""
    print("🔍 Checking available resources...")
    
    # Demo login
    print("\n1. Getting auth token...")
    response = requests.post(f"{BASE_URL}/auth/demo-login")
    if response.status_code != 200:
        print(f"❌ Demo login failed: {response.status_code}")
        return
    
    token = response.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Auth token obtained")
    
    # Get rooms
    print("\n2. Getting rooms...")
    response = requests.get(f"{BASE_URL}/facilities/rooms", headers=headers)
    if response.status_code == 200:
        rooms = response.json()
        print(f"✅ Found {len(rooms)} rooms:")
        for room in rooms:
            print(f"   - Room {room['room_id']}: {room['number']} (capacity: {room['capacity']})")
    else:
        print(f"❌ Failed to get rooms: {response.status_code}")
        return
    
    # Get time slots
    print(f"\n3. Getting time slots...")
    response = requests.get(f"{BASE_URL}/facilities/slots", headers=headers)
    if response.status_code == 200:
        slots = response.json()
        print(f"✅ Found {len(slots)} time slots:")
        for slot in slots:
            print(f"   - Slot {slot['slot_id']}: {slot['start_time']} - {slot['end_time']}")
    else:
        print(f"❌ Failed to get time slots: {response.status_code}")
        return
    
    # Get teachers
    print(f"\n4. Getting teachers...")
    response = requests.get(f"{BASE_URL}/educational/teachers", headers=headers)
    if response.status_code == 200:
        teachers = response.json()
        print(f"✅ Found {len(teachers)} teachers:")
        for teacher in teachers:
            print(f"   - Teacher {teacher['teacher_id']}: {teacher['first_name']} {teacher['last_name']}")
    else:
        print(f"❌ Failed to get teachers: {response.status_code}")
        return
    
    # Get groups
    print(f"\n5. Getting groups...")
    response = requests.get(f"{BASE_URL}/educational/groups", headers=headers)
    if response.status_code == 200:
        groups = response.json()
        print(f"✅ Found {len(groups)} groups:")
        for group in groups:
            print(f"   - Group {group['group_id']}: {group['name']} (generation_type: {group.get('generation_type', 'N/A')})")
    else:
        print(f"❌ Failed to get groups: {response.status_code}")
        return
    
    # Calculate capacity
    print(f"\n6. Resource capacity analysis:")
    print(f"   - Rooms: {len(rooms)}")
    print(f"   - Time slots per day: {len(slots)}")
    print(f"   - Teachers: {len(teachers)}")
    print(f"   - Groups: {len(groups)}")
    print(f"   - Max concurrent lessons per slot: {len(rooms)} (limited by rooms)")
    print(f"   - Max concurrent lessons per day: {len(rooms) * len(slots)}")
    
    if len(rooms) >= len(groups):
        print(f"✅ Sufficient rooms for all groups to have lessons simultaneously")
    else:
        print(f"❌ Not enough rooms for all groups to have lessons simultaneously")
    
    print("\n🎉 Resource check completed!")

if __name__ == "__main__":
    try:
        check_resources()
    except Exception as e:
        print(f"❌ Check failed with error: {e}")
