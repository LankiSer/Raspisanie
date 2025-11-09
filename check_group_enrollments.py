"""Check enrollments for each group to understand diversity."""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def check_group_enrollments():
    """Check enrollments for each group."""
    print("🔍 Checking enrollments for each group...")
    
    # Demo login
    print("\n1. Getting auth token...")
    response = requests.post(f"{BASE_URL}/auth/demo-login")
    if response.status_code != 200:
        print(f"❌ Demo login failed: {response.status_code}")
        return
    
    token = response.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Auth token obtained")
    
    # Get all data
    print("\n2. Getting all data...")
    
    # Get enrollments
    response = requests.get(f"{BASE_URL}/educational/enrollments", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get enrollments: {response.status_code}")
        return
    enrollments = response.json()
    
    # Get course assignments
    response = requests.get(f"{BASE_URL}/educational/course-assignments", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get course assignments: {response.status_code}")
        return
    assignments = response.json()
    
    # Get courses
    response = requests.get(f"{BASE_URL}/educational/courses", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get courses: {response.status_code}")
        return
    courses = response.json()
    
    # Get teachers
    response = requests.get(f"{BASE_URL}/educational/teachers", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get teachers: {response.status_code}")
        return
    teachers = response.json()
    
    # Get groups
    response = requests.get(f"{BASE_URL}/educational/groups", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get groups: {response.status_code}")
        return
    groups = response.json()
    
    # Create lookup dictionaries
    assignments_dict = {a['assignment_id']: a for a in assignments}
    courses_dict = {c['course_id']: c for c in courses}
    teachers_dict = {t['teacher_id']: t for t in teachers}
    groups_dict = {g['group_id']: g for g in groups}
    
    # Group enrollments by group
    print(f"\n3. Enrollments by group:")
    group_enrollments = {}
    for enrollment in enrollments:
        group_id = enrollment['group_id']
        if group_id not in group_enrollments:
            group_enrollments[group_id] = []
        group_enrollments[group_id].append(enrollment)
    
    for group_id, group_enrollments_list in group_enrollments.items():
        group = groups_dict.get(group_id)
        group_name = group['name'] if group else f"Group {group_id}"
        print(f"\n   {group_name} (ID: {group_id}):")
        
        for i, enrollment in enumerate(group_enrollments_list):
            assignment = assignments_dict.get(enrollment['assignment_id'])
            if assignment:
                course = courses_dict.get(assignment['course_id'])
                teacher = teachers_dict.get(assignment['teacher_id'])
                
                if course and teacher:
                    print(f"     {i+1}. {course['name']} with {teacher['first_name']} {teacher['last_name']} ({enrollment['planned_hours']} hours)")
                else:
                    print(f"     {i+1}. Invalid assignment {enrollment['assignment_id']}")
            else:
                print(f"     {i+1}. Assignment {enrollment['assignment_id']} not found")
    
    # Check diversity
    print(f"\n4. Diversity analysis:")
    for group_id, group_enrollments_list in group_enrollments.items():
        group = groups_dict.get(group_id)
        group_name = group['name'] if group else f"Group {group_id}"
        
        # Count unique courses and teachers
        unique_courses = set()
        unique_teachers = set()
        
        for enrollment in group_enrollments_list:
            assignment = assignments_dict.get(enrollment['assignment_id'])
            if assignment:
                course = courses_dict.get(assignment['course_id'])
                teacher = teachers_dict.get(assignment['teacher_id'])
                
                if course:
                    unique_courses.add(course['name'])
                if teacher:
                    unique_teachers.add(f"{teacher['first_name']} {teacher['last_name']}")
        
        print(f"   {group_name}: {len(unique_courses)} unique courses, {len(unique_teachers)} unique teachers")
        print(f"     Courses: {', '.join(sorted(unique_courses))}")
        print(f"     Teachers: {', '.join(sorted(unique_teachers))}")
    
    print("\n🎉 Group enrollments check completed!")

if __name__ == "__main__":
    try:
        check_group_enrollments()
    except Exception as e:
        print(f"❌ Check failed with error: {e}")
