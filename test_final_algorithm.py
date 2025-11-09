"""Final test of the improved scheduling algorithm."""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def test_final_algorithm():
    """Test the final improved scheduling algorithm."""
    print("🎯 Testing Final Improved Scheduling Algorithm")
    print("=" * 60)
    
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
    
    # Test generation with improved algorithm
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
    
    print(f"\n3. Running improved generation algorithm...")
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
    
    # Analyze the results
    print(f"\n4. Analyzing results...")
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
        
        # Analyze each group
        print(f"\n5. Group Analysis:")
        groups_analysis = {}
        for key, group_lessons in sorted(lessons_by_group_day.items()):
            group_name, date = key.split('_', 1)
            if group_name not in groups_analysis:
                groups_analysis[group_name] = []
            groups_analysis[group_name].append({
                'date': date,
                'lessons': len(group_lessons),
                'times': [lesson['start_time'] for lesson in group_lessons],
                'rooms': [lesson['room_number'] for lesson in group_lessons],
                'courses': [lesson['course_name'] for lesson in group_lessons],
                'teachers': [lesson['teacher_name'] for lesson in group_lessons]
            })
        
        for group_name, days_data in groups_analysis.items():
            print(f"\n   📚 {group_name}:")
            total_lessons = sum(day['lessons'] for day in days_data)
            unique_rooms = set()
            unique_courses = set()
            unique_teachers = set()
            
            for day_data in days_data:
                unique_rooms.update(day_data['rooms'])
                unique_courses.update(day_data['courses'])
                unique_teachers.update(day_data['teachers'])
                print(f"     {day_data['date']}: {day_data['lessons']} lessons ({', '.join(day_data['times'])})")
            
            print(f"     Total: {total_lessons} lessons, {len(unique_rooms)} rooms, {len(unique_courses)} courses, {len(unique_teachers)} teachers")
        
        # Overall statistics
        print(f"\n6. Overall Statistics:")
        all_groups = set()
        all_days = set()
        all_rooms = set()
        all_courses = set()
        all_teachers = set()
        
        for lesson in lessons:
            all_groups.add(lesson.get('group_name', 'Unknown'))
            all_days.add(lesson.get('date', 'Unknown'))
            all_rooms.add(lesson.get('room_number', 'Unknown'))
            all_courses.add(lesson.get('course_name', 'Unknown'))
            all_teachers.add(lesson.get('teacher_name', 'Unknown'))
        
        print(f"   - Groups with lessons: {len(all_groups)}/5")
        print(f"   - Days with lessons: {len(all_days)}/5")
        print(f"   - Rooms used: {len(all_rooms)}/5")
        print(f"   - Courses taught: {len(all_courses)}")
        print(f"   - Teachers involved: {len(all_teachers)}/5")
        
        # Success criteria
        print(f"\n7. Success Criteria:")
        success_criteria = [
            (len(all_groups) == 5, f"All 5 groups have lessons: {len(all_groups)}/5"),
            (len(all_days) >= 5, f"All 5 weekdays covered: {len(all_days)}/5"),
            (len(all_rooms) == 5, f"All 5 rooms used: {len(all_rooms)}/5"),
            (len(all_teachers) >= 2, f"Multiple teachers involved: {len(all_teachers)}/5"),
            (len(lessons) >= 50, f"Sufficient lessons generated: {len(lessons)}")
        ]
        
        all_passed = True
        for passed, message in success_criteria:
            status = "✅" if passed else "❌"
            print(f"   {status} {message}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print(f"\n🎉 ALL SUCCESS CRITERIA PASSED!")
            print(f"   The improved scheduling algorithm is working perfectly!")
        else:
            print(f"\n⚠️  Some success criteria failed. Algorithm needs further improvement.")
        
    else:
        print(f"❌ Failed to get lessons: {response.status_code}")
    
    print(f"\n🎯 Final algorithm test completed!")

if __name__ == "__main__":
    try:
        test_final_algorithm()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
