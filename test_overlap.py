#!/usr/bin/env python3
"""
Test script to verify the overlap detection functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import check_schedule_overlaps, Lesson, LessonSchedule

def test_overlap_detection():
    """Test various overlap scenarios"""
    
    print("🧪 Testing overlap detection...")
    
    # Test Case 1: No overlaps
    print("\n📋 Test Case 1: No overlaps")
    lessons_no_overlap = [
        Lesson(
            name="ریاضی",
            units=3,
            schedules=[
                LessonSchedule(day="شنبه", start_time="08:00", end_time="10:00")
            ]
        ),
        Lesson(
            name="فیزیک", 
            units=3,
            schedules=[
                LessonSchedule(day="شنبه", start_time="10:00", end_time="12:00")
            ]
        )
    ]
    
    errors = check_schedule_overlaps(lessons_no_overlap)
    assert len(errors) == 0, f"Expected no errors, got: {errors}"
    print("✅ PASS: No overlaps detected correctly")
    
    # Test Case 2: Clear overlap
    print("\n📋 Test Case 2: Clear overlap")
    lessons_with_overlap = [
        Lesson(
            name="ریاضی",
            units=3, 
            schedules=[
                LessonSchedule(day="شنبه", start_time="08:00", end_time="12:00")
            ]
        ),
        Lesson(
            name="فیزیک",
            units=3,
            schedules=[
                LessonSchedule(day="شنبه", start_time="10:00", end_time="14:00")
            ]
        )
    ]
    
    errors = check_schedule_overlaps(lessons_with_overlap)
    assert len(errors) == 1, f"Expected 1 error, got {len(errors)}: {errors}"
    assert "ریاضی" in errors[0] and "فیزیک" in errors[0], f"Error message missing lesson names: {errors[0]}"
    print("✅ PASS: Overlap detected correctly")
    
    # Test Case 3: Different days (no overlap)
    print("\n📋 Test Case 3: Different days (no overlap)")
    lessons_different_days = [
        Lesson(
            name="ریاضی",
            units=3,
            schedules=[
                LessonSchedule(day="شنبه", start_time="08:00", end_time="12:00")
            ]
        ),
        Lesson(
            name="فیزیک",
            units=3,
            schedules=[
                LessonSchedule(day="یکشنبه", start_time="08:00", end_time="12:00")
            ]
        )
    ]
    
    errors = check_schedule_overlaps(lessons_different_days)
    assert len(errors) == 0, f"Expected no errors, got: {errors}"
    print("✅ PASS: Different days handled correctly")
    
    # Test Case 4: Edge case - touching times (no overlap)
    print("\n📋 Test Case 4: Edge case - touching times")
    lessons_touching = [
        Lesson(
            name="ریاضی",
            units=3,
            schedules=[
                LessonSchedule(day="شنبه", start_time="08:00", end_time="10:00")
            ]
        ),
        Lesson(
            name="فیزیک",
            units=3,
            schedules=[
                LessonSchedule(day="شنبه", start_time="10:00", end_time="12:00")
            ]
        )
    ]
    
    errors = check_schedule_overlaps(lessons_touching)
    assert len(errors) == 0, f"Expected no errors for touching times, got: {errors}"
    print("✅ PASS: Touching times handled correctly")
    
    # Test Case 5: Multiple overlaps
    print("\n📋 Test Case 5: Multiple overlaps")
    lessons_multiple_overlaps = [
        Lesson(
            name="ریاضی",
            units=3,
            schedules=[
                LessonSchedule(day="شنبه", start_time="08:00", end_time="12:00")
            ]
        ),
        Lesson(
            name="فیزیک",
            units=3,
            schedules=[
                LessonSchedule(day="شنبه", start_time="10:00", end_time="14:00")
            ]
        ),
        Lesson(
            name="شیمی",
            units=2,
            schedules=[
                LessonSchedule(day="شنبه", start_time="11:00", end_time="13:00")
            ]
        )
    ]
    
    errors = check_schedule_overlaps(lessons_multiple_overlaps)
    assert len(errors) >= 2, f"Expected at least 2 errors, got {len(errors)}: {errors}"
    print(f"✅ PASS: Multiple overlaps detected ({len(errors)} conflicts)")
    
    print("\n🎉 All tests passed! Overlap detection is working correctly.")

if __name__ == "__main__":
    test_overlap_detection()