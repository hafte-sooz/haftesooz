import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import create_schedule_chart, Lesson, LessonSchedule


def run_smoke():
    lessons = [
        Lesson(name="ریاضی", units=3, schedules=[
            LessonSchedule(day="یکشنبه", start_time="10:00", end_time="12:00"),
            LessonSchedule(day="پنج‌شنبه", start_time="18:00", end_time="20:00")
        ]),
        Lesson(name="فیزیک", units=2, schedules=[
            LessonSchedule(day="سه‌شنبه", start_time="08:00", end_time="10:00")
        ])
    ]

    filename = create_schedule_chart(lessons)
    print("Generated:", filename)


if __name__ == '__main__':
    run_smoke()
