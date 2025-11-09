"""Test daily generation for all groups."""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def test_daily_generation():
    """Test generation with all groups having lessons daily."""
    print("🧪 Testing daily generation for all groups...")
    
    # Demo login
    print("\n1. Getting auth token...")
    response = requests.post(f"{BASE_URL}/auth/demo-login")
    if response.status_code != 200:
        print(f"❌ Demo login failed: {response.status_code}")
        return
    
    token = response.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Auth token obtained")
    
    # Get current week dates
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    start_date = monday.strftime('%Y-%m-%d')
    end_date = sunday.strftime('%Y-%m-%d')
    
    print(f"\n2. Testing generation for week {start_date} to {end_date}")
    
    # Test generation with daily lessons for all groups
    payload = {
        "term_id": 1,
        "from_date": start_date,
        "to_date": end_date,
        "ruleset": {
            "respect_availability": True,
            "max_lessons_per_day_group": 6,
            "max_lessons_per_day_teacher": 8,
            "room_capacity_check": True,
            "enable_block_scheduling": True,
            "max_blocks_per_day": 5,  # Allow up to 5 blocks per day (one per group)
            "min_gap_between_blocks": 1
        }
    }
    
    print(f"\n3. Running generation with daily lessons for all groups...")
    response = requests.post(f"{BASE_URL}/generation/run", headers=headers, json=payload)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Generation successful!")
        print(f"   - Created lessons: {result.get('created_lessons', 0)}")
        print(f"   - Total blocks: {result.get('total_blocks', 0)}")
        print(f"   - Message: {result.get('message', 'No message')}")
    else:
        print(f"❌ Generation failed: {response.text}")
        return
    
    # Check lessons by group and day
    print(f"\n4. Checking lessons by group and day...")
    response = requests.get(f"{BASE_URL}/lessons/term?start_date={start_date}&end_date={end_date}", headers=headers)
    if response.status_code == 200:
        lessons = response.json()
        print(f"✅ Found {len(lessons)} lessons total")
        
        # Group lessons by group and day
        lessons_by_group_day = {}
        for lesson in lessons:
            group_name = lesson.get('group_name', 'Unknown')
            date = lesson.get('date', 'Unknown')
            key = f"{group_name}_{date}"
            if key not in lessons_by_group_day:
                lessons_by_group_day[key] = []
            lessons_by_group_day[key].append(lesson)
        
        print(f"\n5. Lessons by group and day:")
        for key, group_lessons in sorted(lessons_by_group_day.items()):
            group_name, date = key.split('_', 1)
            print(f"   {group_name} on {date}: {len(group_lessons)} lessons")
            for lesson in group_lessons:
                print(f"     - {lesson['start_time']}: {lesson['course_name']} with {lesson['teacher_name']} in room {lesson['room_number']}")
        
        # Check if all groups have lessons every day
        groups_with_lessons = set()
        days_with_lessons = set()
        for lesson in lessons:
            groups_with_lessons.add(lesson.get('group_name', 'Unknown'))
            days_with_lessons.add(lesson.get('date', 'Unknown'))
        
        print(f"\n6. Coverage analysis:")
        print(f"   - Groups with lessons: {len(groups_with_lessons)}")
        for group in sorted(groups_with_lessons):
            print(f"     - {group}")
        
        print(f"   - Days with lessons: {len(days_with_lessons)}")
        for day in sorted(days_with_lessons):
            print(f"     - {day}")
        
        # Check diversity
        print(f"\n7. Diversity analysis:")
        courses_used = set()
        teachers_used = set()
        rooms_used = set()
        
        for lesson in lessons:
            courses_used.add(lesson.get('course_name', 'Unknown'))
            teachers_used.add(lesson.get('teacher_name', 'Unknown'))
            rooms_used.add(lesson.get('room_number', 'Unknown'))
        
        print(f"   - Unique courses: {len(courses_used)}")
        print(f"     {', '.join(sorted(courses_used))}")
        print(f"   - Unique teachers: {len(teachers_used)}")
        print(f"     {', '.join(sorted(teachers_used))}")
        print(f"   - Unique rooms: {len(rooms_used)}")
        print(f"     {', '.join(sorted(rooms_used))}")
        
        if len(groups_with_lessons) == 5 and len(days_with_lessons) >= 5:
            print("✅ All groups have lessons across multiple days!")
        else:
            print(f"❌ Not all groups have lessons: {len(groups_with_lessons)}/5 groups, {len(days_with_lessons)} days")
    else:
        print(f"❌ Failed to get lessons: {response.status_code}")
    
    print("\n🎉 Daily generation test completed!")

if __name__ == "__main__":
    try:
        test_daily_generation()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
