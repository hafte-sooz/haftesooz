let lessonCount = 1;
let scheduleCounters = { 0: 1 };

// Persian to English number conversion for form processing
function convertPersianToEnglish(str) {
  const persianNumbers = ["۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹"];
  const englishNumbers = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"];

  for (let i = 0; i < persianNumbers.length; i++) {
    str = str.replace(new RegExp(persianNumbers[i], "g"), englishNumbers[i]);
  }
  return str;
}

// Check for schedule overlaps across all lessons
function checkScheduleOverlaps() {
  const allSchedules = [];
  const lessonItems = document.querySelectorAll(".lesson-item");

  // Collect all schedules
  lessonItems.forEach((lessonItem) => {
    const lessonName =
      lessonItem.querySelector('input[name^="lesson-name-"]')?.value || "";
    const scheduleItems = lessonItem.querySelectorAll(".schedule-item");

    scheduleItems.forEach((scheduleItem) => {
      const daySelect = scheduleItem.querySelector('select[name^="day-"]');
      const startSelect = scheduleItem.querySelector(
        'select[name^="start-time-"]'
      );
      const endSelect = scheduleItem.querySelector('select[name^="end-time-"]');

      if (daySelect?.value && startSelect?.value && endSelect?.value) {
        allSchedules.push({
          lessonName: lessonName,
          day: daySelect.value,
          startTime: startSelect.value,
          endTime: endSelect.value,
          element: scheduleItem,
        });
      }
    });
  });

  // Check for overlaps
  const conflicts = [];
  for (let i = 0; i < allSchedules.length; i++) {
    for (let j = i + 1; j < allSchedules.length; j++) {
      const schedule1 = allSchedules[i];
      const schedule2 = allSchedules[j];

      // Skip if different days
      if (schedule1.day !== schedule2.day) continue;

      const start1 = parseInt(schedule1.startTime.split(":")[0]);
      const end1 = parseInt(schedule1.endTime.split(":")[0]);
      const start2 = parseInt(schedule2.startTime.split(":")[0]);
      const end2 = parseInt(schedule2.endTime.split(":")[0]);

      // Check for overlap
      if (start1 < end2 && start2 < end1) {
        conflicts.push({
          lesson1: schedule1.lessonName,
          lesson2: schedule2.lessonName,
          day: schedule1.day,
          time1: `${schedule1.startTime}-${schedule1.endTime}`,
          time2: `${schedule2.startTime}-${schedule2.endTime}`,
          element1: schedule1.element,
          element2: schedule2.element,
        });
      }
    }
  }

  return conflicts;
}

// Highlight conflicting schedules
function highlightConflicts(conflicts) {
  // Clear previous highlights
  document.querySelectorAll(".schedule-item").forEach((item) => {
    item.classList.remove("conflict");
  });

  // Add conflict highlights
  conflicts.forEach((conflict) => {
    conflict.element1.classList.add("conflict");
    conflict.element2.classList.add("conflict");
  });
}

// Validate schedule changes in real-time
function validateScheduleChange(changedElement) {
  const conflicts = checkScheduleOverlaps();
  highlightConflicts(conflicts);

  if (conflicts.length > 0) {
    const conflictMessages = conflicts.map(
      (conflict) =>
        `تداخل: ${conflict.lesson1} و ${conflict.lesson2} در ${conflict.day} (${conflict.time1} و ${conflict.time2})`
    );

    // Show warning message
    showConflictWarning(conflictMessages);
    return false;
  } else {
    hideConflictWarning();
    return true;
  }
}

// Show conflict warning
function showConflictWarning(messages) {
  let warningDiv = document.getElementById("conflict-warning");
  if (!warningDiv) {
    warningDiv = document.createElement("div");
    warningDiv.id = "conflict-warning";
    warningDiv.className = "conflict-warning";

    const formSection = document.querySelector(".form-section");
    formSection.insertBefore(warningDiv, formSection.firstChild);
  }

  warningDiv.innerHTML = `
    <div class="warning-content">
      <h4>⚠️ تداخل زمانی شناسایی شد:</h4>
      <ul>
        ${messages.map((msg) => `<li>${msg}</li>`).join("")}
      </ul>
      <p>لطفاً زمان‌بندی دروس را تصحیح کنید.</p>
    </div>
  `;
  warningDiv.style.display = "block";
}

// Hide conflict warning
function hideConflictWarning() {
  const warningDiv = document.getElementById("conflict-warning");
  if (warningDiv) {
    warningDiv.style.display = "none";
  }
}

// Restore form data from server response
function restoreFormData(lessonsData) {
  if (!lessonsData || lessonsData.length === 0) return;

  // Clear existing lessons except the first one
  const container = document.getElementById("lessons-container");
  const existingLessons = container.querySelectorAll(".lesson-item");
  for (let i = existingLessons.length - 1; i > 0; i--) {
    existingLessons[i].remove();
  }

  // Reset counters
  lessonCount = 1;
  scheduleCounters = { 0: 1 };

  // Restore each lesson
  lessonsData.forEach((lessonData, lessonIndex) => {
    // Add new lesson if needed (except for the first one)
    if (lessonIndex > 0) {
      addLesson();
    }

    // Restore lesson basic info
    const nameInput = document.querySelector(
      `input[name="lesson-name-${lessonIndex}"]`
    );
    const unitsInput = document.querySelector(
      `input[name="lesson-units-${lessonIndex}"]`
    );

    if (nameInput) nameInput.value = lessonData.name;
    if (unitsInput) unitsInput.value = lessonData.units;

    // Clear existing schedules for this lesson
    const schedulesContainer = document.querySelector(
      `[data-lesson="${lessonIndex}"]`
    );
    const existingSchedules =
      schedulesContainer.querySelectorAll(".schedule-item");
    for (let i = existingSchedules.length - 1; i > 0; i--) {
      existingSchedules[i].remove();
    }

    // Restore schedules
    lessonData.schedules.forEach((scheduleData, scheduleIndex) => {
      // Add new schedule if needed (except for the first one)
      if (scheduleIndex > 0) {
        addSchedule(lessonIndex);
      }

      // Set schedule values
      const daySelect = document.querySelector(
        `select[name="day-${lessonIndex}-${scheduleIndex}"]`
      );
      const startSelect = document.querySelector(
        `select[name="start-time-${lessonIndex}-${scheduleIndex}"]`
      );
      const endSelect = document.querySelector(
        `select[name="end-time-${lessonIndex}-${scheduleIndex}"]`
      );

      if (daySelect) daySelect.value = scheduleData.day;
      if (startSelect) startSelect.value = scheduleData.start_time;
      if (endSelect) endSelect.value = scheduleData.end_time;
    });
  });

  // Run validation after restoration
  setTimeout(() => {
    validateScheduleChange(null);
  }, 100);
}

function addLesson() {
  const container = document.getElementById("lessons-container");
  const lessonIndex = lessonCount;
  scheduleCounters[lessonIndex] = 1;

  const lessonHtml = `
        <div class="lesson-item">
            <h3>درس ${lessonIndex + 1}</h3>
            <div class="lesson-basic-info">
                <div class="form-group">
                    <label for="lesson-name-${lessonIndex}">نام درس:</label>
                    <input type="text" id="lesson-name-${lessonIndex}" name="lesson-name-${lessonIndex}" required>
                </div>
                <div class="form-group">
                    <label for="lesson-units-${lessonIndex}">تعداد واحد:</label>
                    <input type="number" id="lesson-units-${lessonIndex}" name="lesson-units-${lessonIndex}" min="1" max="6" required>
                </div>
            </div>
            
            <div class="schedules-container" data-lesson="${lessonIndex}">
                <h4>زمان‌بندی دروس:</h4>
                <div class="schedule-item">
                    <div class="form-group">
                        <label>روز:</label>
                        <select name="day-${lessonIndex}-0" required>
                            <option value="">انتخاب کنید</option>
                            <option value="شنبه">شنبه</option>
                            <option value="یکشنبه">یکشنبه</option>
                            <option value="دوشنبه">دوشنبه</option>
                            <option value="سه‌شنبه">سه‌شنبه</option>
                            <option value="چهارشنبه">چهارشنبه</option>
                            <option value="پنج‌شنبه">پنج‌شنبه</option>
                            <option value="جمعه">جمعه</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>ساعت شروع:</label>
                        <select name="start-time-${lessonIndex}-0" required>
                            <option value="">انتخاب کنید</option>
                            <option value="06:00">۰۶:۰۰</option>
                            <option value="07:00">۰۷:۰۰</option>
                            <option value="08:00">۰۸:۰۰</option>
                            <option value="09:00">۰۹:۰۰</option>
                            <option value="10:00">۱۰:۰۰</option>
                            <option value="11:00">۱۱:۰۰</option>
                            <option value="12:00">۱۲:۰۰</option>
                            <option value="13:00">۱۳:۰۰</option>
                            <option value="14:00">۱۴:۰۰</option>
                            <option value="15:00">۱۵:۰۰</option>
                            <option value="16:00">۱۶:۰۰</option>
                            <option value="17:00">۱۷:۰۰</option>
                            <option value="18:00">۱۸:۰۰</option>
                            <option value="19:00">۱۹:۰۰</option>
                            <option value="20:00">۲۰:۰۰</option>
                            <option value="21:00">۲۱:۰۰</option>
                            <option value="22:00">۲۲:۰۰</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>ساعت پایان:</label>
                        <select name="end-time-${lessonIndex}-0" required>
                            <option value="">انتخاب کنید</option>
                            <option value="07:00">۰۷:۰۰</option>
                            <option value="08:00">۰۸:۰۰</option>
                            <option value="09:00">۰۹:۰۰</option>
                            <option value="10:00">۱۰:۰۰</option>
                            <option value="11:00">۱۱:۰۰</option>
                            <option value="12:00">۱۲:۰۰</option>
                            <option value="13:00">۱۳:۰۰</option>
                            <option value="14:00">۱۴:۰۰</option>
                            <option value="15:00">۱۵:۰۰</option>
                            <option value="16:00">۱۶:۰۰</option>
                            <option value="17:00">۱۷:۰۰</option>
                            <option value="18:00">۱۸:۰۰</option>
                            <option value="19:00">۱۹:۰۰</option>
                            <option value="20:00">۲۰:۰۰</option>
                            <option value="21:00">۲۱:۰۰</option>
                            <option value="22:00">۲۲:۰۰</option>
                            <option value="23:00">۲۳:۰۰</option>
                        </select>
                    </div>
                    <button type="button" class="btn btn-danger remove-schedule" onclick="removeSchedule(this)">حذف زمان</button>
                </div>
                <button type="button" class="btn btn-secondary add-schedule" onclick="addSchedule(${lessonIndex})">افزودن زمان جدید</button>
            </div>
            <button type="button" class="btn btn-danger remove-lesson" onclick="removeLesson(this)">حذف درس</button>
        </div>
    `;

  container.insertAdjacentHTML("beforeend", lessonHtml);
  lessonCount++;
}

function removeLesson(button) {
  const lessonItem = button.closest(".lesson-item");
  if (document.querySelectorAll(".lesson-item").length > 1) {
    lessonItem.remove();
    updateLessonNumbers();
  } else {
    alert("حداقل یک درس باید وجود داشته باشد");
  }
}

function addSchedule(lessonIndex) {
  const schedulesContainer = document.querySelector(
    `[data-lesson="${lessonIndex}"]`
  );
  const scheduleIndex = scheduleCounters[lessonIndex];

  const scheduleHtml = `
        <div class="schedule-item">
            <div class="form-group">
                <label>روز:</label>
                <select name="day-${lessonIndex}-${scheduleIndex}" required>
                    <option value="">انتخاب کنید</option>
                    <option value="شنبه">شنبه</option>
                    <option value="یکشنبه">یکشنبه</option>
                    <option value="دوشنبه">دوشنبه</option>
                    <option value="سه‌شنبه">سه‌شنبه</option>
                    <option value="چهارشنبه">چهارشنبه</option>
                    <option value="پنج‌شنبه">پنج‌شنبه</option>
                    <option value="جمعه">جمعه</option>
                </select>
            </div>
            <div class="form-group">
                <label>ساعت شروع:</label>
                <select name="start-time-${lessonIndex}-${scheduleIndex}" required>
                    <option value="">انتخاب کنید</option>
                    <option value="06:00">۰۶:۰۰</option>
                    <option value="07:00">۰۷:۰۰</option>
                    <option value="08:00">۰۸:۰۰</option>
                    <option value="09:00">۰۹:۰۰</option>
                    <option value="10:00">۱۰:۰۰</option>
                    <option value="11:00">۱۱:۰۰</option>
                    <option value="12:00">۱۲:۰۰</option>
                    <option value="13:00">۱۳:۰۰</option>
                    <option value="14:00">۱۴:۰۰</option>
                    <option value="15:00">۱۵:۰۰</option>
                    <option value="16:00">۱۶:۰۰</option>
                    <option value="17:00">۱۷:۰۰</option>
                    <option value="18:00">۱۸:۰۰</option>
                    <option value="19:00">۱۹:۰۰</option>
                    <option value="20:00">۲۰:۰۰</option>
                    <option value="21:00">۲۱:۰۰</option>
                    <option value="22:00">۲۲:۰۰</option>
                </select>
            </div>
            <div class="form-group">
                <label>ساعت پایان:</label>
                <select name="end-time-${lessonIndex}-${scheduleIndex}" required>
                    <option value="">انتخاب کنید</option>
                    <option value="07:00">۰۷:۰۰</option>
                    <option value="08:00">۰۸:۰۰</option>
                    <option value="09:00">۰۹:۰۰</option>
                    <option value="10:00">۱۰:۰۰</option>
                    <option value="11:00">۱۱:۰۰</option>
                    <option value="12:00">۱۲:۰۰</option>
                    <option value="13:00">۱۳:۰۰</option>
                    <option value="14:00">۱۴:۰۰</option>
                    <option value="15:00">۱۵:۰۰</option>
                    <option value="16:00">۱۶:۰۰</option>
                    <option value="17:00">۱۷:۰۰</option>
                    <option value="18:00">۱۸:۰۰</option>
                    <option value="19:00">۱۹:۰۰</option>
                    <option value="20:00">۲۰:۰۰</option>
                    <option value="21:00">۲۱:۰۰</option>
                    <option value="22:00">۲۲:۰۰</option>
                    <option value="23:00">۲۳:۰۰</option>
                </select>
            </div>
            <button type="button" class="btn btn-danger remove-schedule" onclick="removeSchedule(this)">حذف زمان</button>
        </div>
    `;

  const addButton = schedulesContainer.querySelector(".add-schedule");
  addButton.insertAdjacentHTML("beforebegin", scheduleHtml);
  scheduleCounters[lessonIndex]++;
}

function removeSchedule(button) {
  const scheduleItem = button.closest(".schedule-item");
  const schedulesContainer = button.closest(".schedules-container");

  if (schedulesContainer.querySelectorAll(".schedule-item").length > 1) {
    scheduleItem.remove();
  } else {
    alert("حداقل یک زمان‌بندی برای هر درس باید وجود داشته باشد");
  }
}

function updateLessonNumbers() {
  const lessons = document.querySelectorAll(".lesson-item");
  lessons.forEach((lesson, index) => {
    const title = lesson.querySelector("h3");
    title.textContent = `درس ${index + 1}`;
  });
}

// Form submission handler
document.getElementById("lessonForm").addEventListener("submit", function (e) {
  // On submit: build the lessons_data payload and let the browser perform a normal POST
  // This ensures the server-rendered page is fully loaded and inline scripts (restoreFormData)
  // are executed by the browser so form data can be rehydrated.
  const conflicts = checkScheduleOverlaps();
  if (conflicts.length > 0) {
    // Prevent submit when conflicts exist
    e.preventDefault();
    highlightConflicts(conflicts);
    const conflictMessages = conflicts.map(
      (conflict) =>
        `تداخل: ${conflict.lesson1} و ${conflict.lesson2} در ${conflict.day} (${conflict.time1} و ${conflict.time2})`
    );
    showConflictWarning(conflictMessages);
    alert("لطفاً ابتدا تداخل‌های زمانی را برطرف کنید.");
    return;
  }

  // Build lessons payload and set hidden input; allow submit to proceed
  const lessons = [];
  const lessonItems = document.querySelectorAll(".lesson-item");

  lessonItems.forEach((lessonItem, lessonIndex) => {
    const nameInput = lessonItem.querySelector(`input[name^="lesson-name-"]`);
    const unitsInput = lessonItem.querySelector(`input[name^="lesson-units-"]`);

    if (!nameInput || !unitsInput) return;

    const lesson = {
      name: nameInput.value.trim(),
      units: parseInt(unitsInput.value) || 0,
      schedules: [],
    };

    const scheduleItems = lessonItem.querySelectorAll(".schedule-item");
    scheduleItems.forEach((scheduleItem) => {
      const daySelect = scheduleItem.querySelector('select[name^="day-"]');
      const startSelect = scheduleItem.querySelector(
        'select[name^="start-time-"]'
      );
      const endSelect = scheduleItem.querySelector('select[name^="end-time-"]');

      if (
        daySelect &&
        startSelect &&
        endSelect &&
        daySelect.value &&
        startSelect.value &&
        endSelect.value
      ) {
        lesson.schedules.push({
          day: daySelect.value,
          start_time: startSelect.value,
          end_time: endSelect.value,
        });
      }
    });

    if (lesson.name && lesson.units && lesson.schedules.length > 0)
      lessons.push(lesson);
  });

  if (lessons.length === 0) {
    e.preventDefault();
    alert("لطفاً حداقل یک درس با زمان‌بندی معتبر وارد کنید");
    return;
  }

  // Put JSON into hidden input so server receives it when browser submits the form normally
  const hidden = document.getElementById("lessons_data");
  if (hidden) {
    hidden.value = JSON.stringify(lessons);
  }

  // Allow form to submit normally (no fetch). Browser will render the server response and execute scripts.
});

// Add event listeners for time validation and conflict detection
document.addEventListener("change", function (e) {
  // Check for time order validation
  if (e.target.name && e.target.name.includes("start-time-")) {
    const scheduleItem = e.target.closest(".schedule-item");
    const endSelect = scheduleItem.querySelector('select[name*="end-time-"]');
    const startTime = e.target.value;

    if (startTime && endSelect.value) {
      const startHour = parseInt(startTime.split(":")[0]);
      const endHour = parseInt(endSelect.value.split(":")[0]);

      if (endHour <= startHour) {
        alert("ساعت پایان باید بعد از ساعت شروع باشد");
        endSelect.value = "";
      }
    }

    // Check for schedule conflicts
    validateScheduleChange(e.target);
  }

  if (e.target.name && e.target.name.includes("end-time-")) {
    const scheduleItem = e.target.closest(".schedule-item");
    const startSelect = scheduleItem.querySelector(
      'select[name*="start-time-"]'
    );
    const endTime = e.target.value;

    if (endTime && startSelect.value) {
      const startHour = parseInt(startSelect.value.split(":")[0]);
      const endHour = parseInt(endTime.split(":")[0]);

      if (endHour <= startHour) {
        alert("ساعت پایان باید بعد از ساعت شروع باشد");
        e.target.value = "";
        return;
      }
    }

    // Check for schedule conflicts
    validateScheduleChange(e.target);
  }

  // Check for conflicts when day changes
  if (e.target.name && e.target.name.includes("day-")) {
    validateScheduleChange(e.target);
  }
});

document.addEventListener("click", function (e) {
  const lessonEl = e.target.closest && e.target.closest(".lesson-item");
  if (!lessonEl) return;
  const header = lessonEl.querySelector("h3");
  if (!header) return;
  if (header.contains(e.target)) {
    const lessonItem = header.closest(".lesson-item");
    const container = document.getElementById("lessons-container");
    if (lessonItem && container && container.firstElementChild !== lessonItem) {
      // Move the lesson to the top of the container
      container.insertBefore(lessonItem, container.firstElementChild);
      // Update titles (numbers) after rearrange
      updateLessonNumbers();
    }
  }
});
