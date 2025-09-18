from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import uuid
import os
from typing import List, Optional
import re

# Optional shaping deps: attempt import once at module load so we can use in functions
try:
    import arabic_reshaper as _arabic_reshaper
    from bidi.algorithm import get_display as _bidi_get_display
    BIDI_AVAILABLE = True
except Exception:
    _arabic_reshaper = None
    _bidi_get_display = None
    BIDI_AVAILABLE = False
from pydantic import BaseModel

font_dir = os.path.join(os.path.dirname(__file__), 'static', 'fonts')
regular_font_path = os.path.join(font_dir, 'Vazirmatn-Regular.ttf')
if os.path.exists(regular_font_path):
    PERSIAN_FONT = fm.FontProperties(fname=regular_font_path)
else:
    PERSIAN_FONT = fm.FontProperties(family="sans-serif")

def _maybe_shape_persian(text: str) -> str:
    """Return Persian text reshaped if libraries exist, else return as-is."""
    if not text:
        return text
    if _arabic_reshaper and _bidi_get_display:
        try:
            reshaped = _arabic_reshaper.reshape(text)
            return _bidi_get_display(reshaped)
        except Exception:
            return text
    return text


app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

# Persian day names
PERSIAN_DAYS = {
    "شنبه": 0,
    "یکشنبه": 1,
    "دوشنبه": 2,
    "سه‌شنبه": 3,
    "چهارشنبه": 4,
    "پنج‌شنبه": 5,
    "جمعه": 6
}

DAY_NAMES = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]


class LessonSchedule(BaseModel):
    day: str
    start_time: str
    end_time: str


class Lesson(BaseModel):
    name: str
    units: int
    schedules: List[LessonSchedule]


def _fallback_bidi_approx(text: str) -> str:
    """A conservative bidi fallback for when python-bidi/arabic_reshaper are missing.

    This does not do real shaping. It reverses the order of Arabic/RTL groups while
    leaving numbers and punctuation in place. It's a visual approximation so the
    text appears right-to-left instead of fully garbled.
    """
    # Split text into runs of Arabic (letters) and non-Arabic
    parts = re.findall(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+|[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+", text)
    # Reverse the order of runs so RTL runs appear first
    parts = parts[::-1]
    joined = "".join(parts)
    # Prepend RLM mark to hint rendering direction
    return "\u200F" + joined


def _maybe_shape_persian(text: str) -> str:
    """Shape and bidi-reorder Persian text when possible; otherwise use a fallback.

    - If arabic_reshaper + python-bidi are available, use them for correct shaping and bidi.
    - Otherwise use a conservative approximation that reverses RTL groups and adds RLM.
    """
    if not text:
        return text

    if BIDI_AVAILABLE and _arabic_reshaper and _bidi_get_display:
        try:
            reshaped = _arabic_reshaper.reshape(text)
            return _bidi_get_display(reshaped)
        except Exception:
            # Fall through to approximation
            return _fallback_bidi_approx(text)
    else:
        return _fallback_bidi_approx(text)


def create_schedule_chart(lessons: List[Lesson]) -> str:
    """Create a schedule chart and return the filename.

    Rectangles occupy most of the vertical day cell to match the example image.
    Persian shaping (arabic_reshaper + python-bidi) is used when available.
    """

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib import font_manager

    # Optional RTL shaping libraries
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        bidi_available = True
    except Exception:
        arabic_reshaper = None
        get_display = None
        bidi_available = False

    # Configure matplotlib to use our downloaded Vazirmatn fonts
    # We'll register the local TTF files and create a FontProperties pointing
    # to Vazirmatn-Regular.ttf so we can set it globally and also pass it
    # explicitly to individual text calls when needed.
    try:
        import os
        from matplotlib import rcParams
        from matplotlib import font_manager as fm

        font_dir = os.path.join(os.path.dirname(__file__), 'static', 'fonts')
        regular_font_path = os.path.join(font_dir, 'Vazirmatn-Regular.ttf')

        # Register all TTF files we downloaded (if present)
        for fname in ('Vazirmatn-Light.ttf', 'Vazirmatn-Regular.ttf', 'Vazirmatn-Medium.ttf',
                      'Vazirmatn-SemiBold.ttf', 'Vazirmatn-Bold.ttf'):
            fp = os.path.join(font_dir, fname)
            if os.path.exists(fp):
                fm.fontManager.addfont(fp)

        # Create a FontProperties object for the regular font
        if os.path.exists(regular_font_path):
            persian_font = fm.FontProperties(fname=regular_font_path)
            # Set global default font family to the registered font name
            try:
                rcParams['font.family'] = persian_font.get_name()
            except Exception:
                # Fallback: use the file name if get_name() fails
                rcParams['font.family'] = ['Vazirmatn']
        else:
            # If the regular font isn't present, fall back to generic sans-serif
            rcParams['font.family'] = ['sans-serif']

        # Ensure minus sign renders correctly
        rcParams['axes.unicode_minus'] = False

        # Expose persian_font for use in local scope (optional)
        _PERSIAN_FONT_PROP = persian_font if 'persian_font' in locals() else None

    except Exception as e:
        # If anything goes wrong, use matplotlib defaults but don't crash
        print(f"Warning: could not configure Vazirmatn fonts for matplotlib: {e}")
        try:
            from matplotlib import rcParams
            rcParams['font.family'] = ['sans-serif']
            rcParams['axes.unicode_minus'] = False
        except Exception:
            pass

    plt.rcParams["font.size"] = 16
    plt.rcParams["axes.unicode_minus"] = False

    # Make the figure wider so the schedule is more horizontally stretched
    fig, ax = plt.subplots(figsize=(22, 12))

    # Time slots (6 AM to 10 PM)
    hours = list(range(6, 23))
    hour_labels = [f"{h:02d}:00" for h in hours]

    # Days
    days = DAY_NAMES

    # Set up the grid
    ax.set_xlim(0, len(hours))
    ax.set_ylim(0, len(days))

    # Set ticks and labels with larger fonts
    # Put hour ticks on the top and reverse x-axis so 06:00 is on the right
    ax.set_xticks(range(len(hours)))
    # set labels (we'll apply size/weight reliably with tick_params and Text objects)
    ax.set_xticklabels(hour_labels)
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position('top')
    ax.set_xlim(len(hours), 0)  # reverse x-axis: right -> left (06:00 appears on right)

    # Reserve y positions for days on the main axis but render labels on a twin axis outside the plot
    ax.set_yticks(range(len(days)))
    shaped_days = [_maybe_shape_persian(d) for d in days]
    # Clear main y tick labels so grid lines remain uncluttered
    ax.set_yticklabels([])

    # Create a twin axis for the day labels on the right so they sit outside the chart area
    ax2 = ax.twinx()
    # Mirror limits and ticks, but place the spine just outside the axes using axes coords
    ax2.set_ylim(ax.get_ylim())
    ax2.set_yticks(range(len(days)))
    # Set the day labels (text) then explicitly set their visual size via tick_params
    ax2.set_yticklabels(shaped_days, fontproperties=PERSIAN_FONT)
    # Use tick_params to reliably set label size (some backends ignore fontsize in set_yticklabels)
    ax2.tick_params(axis='y', labelsize=24)
    ax2.yaxis.set_ticks_position('right')
    # Try to position the spine a bit closer so day labels sit nearer the plot but still outside
    try:
        ax2.spines['right'].set_position(('axes', 1.06))
    except Exception:
        try:
            ax2.spines['right'].set_position(('outward', 60))
        except Exception:
            pass
    # Reduce the twin axis frame so it doesn't draw over the plot and add padding
    ax2.set_frame_on(False)
    ax2.tick_params(axis='y', pad=12)
    # Align labels to the right so Persian labels are flush outside the plot;
    # also ensure font weight/size are applied directly on the Text objects
    for lbl in ax2.get_yticklabels():
        lbl.set_ha('right')
        try:
            lbl.set_fontweight('bold')
            lbl.set_fontsize(24)
        except Exception:
            pass
    # We'll adjust layout later once all styling is applied (final subplots_adjust below)

    # Add grid
    ax.grid(True, alpha=0.3)

    # Colors for different lessons
    colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FECA57", "#FF9FF3", "#54A0FF", "#FD79A8"]
    color_index = 0

    # Process each lesson
    for lesson in lessons:
        color = colors[color_index % len(colors)]

        for schedule in lesson.schedules:
            day_name = schedule.day
            if day_name not in PERSIAN_DAYS:
                continue

            day_index = PERSIAN_DAYS[day_name]

            try:
                # Parse time
                start_hour = int(schedule.start_time.split(":")[0])
                end_hour = int(schedule.end_time.split(":")[0])

                # Calculate position
                # Note: because x-axis is reversed, we compute x from left but then rectangles will plot correctly
                start_pos = start_hour - 6  # Offset from 6 AM
                duration = end_hour - start_hour

                # Rectangle should almost cover the vertical day cell (leave a small gap)
                rect_height = 0.92
                rect_y = day_index + (1.0 - rect_height) / 2.0

                if start_pos >= 0 and start_pos < len(hours) and duration > 0:
                    # Create rectangle for the lesson
                    # When x-axis is reversed, patch placement is the same (matplotlib flips view)
                    rect = patches.Rectangle((start_pos, rect_y), duration, rect_height,
                                             linewidth=2, edgecolor="black", facecolor=color, alpha=0.85)
                    ax.add_patch(rect)

                    # Add lesson name and units text. For Persian we may need to reshape and reorder.
                    text_x = start_pos + duration / 2
                    text_y = day_index + 0.5

                    lesson_text = f"{lesson.name}\n({lesson.units} واحد)"
                    display_text = _maybe_shape_persian(lesson_text)

                    # Smart font sizing: measure text in pixels and reduce size until it fits
                    # Make text black and bold. This approach uses the renderer to get
                    # exact extents so we can ensure the label doesn't overflow.
                    # Start with a generous max font size and shrink to fit.
                    max_font = 32
                    min_font = 10

                    # Try to create a sensible multi-line text (split long names reasonably)
                    words = lesson.name.split()
                    if len(words) > 1 and len(lesson.name) > 20 and duration >= 2:
                        mid = len(words) // 2
                        line1 = " ".join(words[:mid])
                        line2 = " ".join(words[mid:])
                        candidate_text = f"{line1}\n{line2}\n({lesson.units} واحد)"
                    else:
                        candidate_text = f"{lesson.name}\n({lesson.units} واحد)"

                    # Place a Text object with an initial large fontsize, then measure
                    txt = ax.text(text_x, text_y, _maybe_shape_persian(candidate_text),
                                  ha="center", va="center", fontsize=max_font,
                                  fontweight="bold", color="black", zorder=3,
                                  fontproperties=PERSIAN_FONT)

                    # Ensure canvas has a renderer available
                    try:
                        fig.canvas.draw()
                        renderer = fig.canvas.get_renderer()

                        # Rectangle bounds in display (pixel) coordinates
                        p0 = ax.transData.transform((start_pos, rect_y))
                        p1 = ax.transData.transform((start_pos + duration, rect_y + rect_height))
                        rect_w_px = abs(p1[0] - p0[0])
                        rect_h_px = abs(p1[1] - p0[1])

                        # Padding inside the rectangle (pixels)
                        pad_px = max(6, rect_w_px * 0.06)

                        # Iteratively reduce fontsize until text fits width and height
                        bbox = txt.get_window_extent(renderer=renderer)
                        current_font = max_font
                        attempts = 0
                        while (bbox.width > (rect_w_px - pad_px) or bbox.height > (rect_h_px - pad_px)) and current_font > min_font and attempts < 10:
                            # Scale font proportionally to available width (conservative)
                            scale = (rect_w_px - pad_px) / max(bbox.width, 1)
                            new_font = max(min_font, int(current_font * scale * 0.95))
                            if new_font >= current_font:
                                new_font = current_font - 1
                            current_font = new_font
                            txt.set_fontsize(current_font)
                            fig.canvas.draw()
                            bbox = txt.get_window_extent(renderer=renderer)
                            attempts += 1

                        # If text still doesn't fit and we used a single-line name, try splitting words again
                        if (bbox.width > (rect_w_px - pad_px) or bbox.height > (rect_h_px - pad_px)) and len(words) > 1:
                            mid = len(words) // 2
                            line1 = " ".join(words[:mid])
                            line2 = " ".join(words[mid:])
                            candidate_text = f"{line1}\n{line2}\n({lesson.units} واحد)"
                            txt.set_text(_maybe_shape_persian(candidate_text))
                            # Reset font and try shrinking again
                            current_font = min(max_font, current_font)
                            txt.set_fontsize(current_font)
                            fig.canvas.draw()
                            bbox = txt.get_window_extent(renderer=renderer)
                            attempts = 0
                            while (bbox.width > (rect_w_px - pad_px) or bbox.height > (rect_h_px - pad_px)) and current_font > min_font and attempts < 10:
                                scale = (rect_w_px - pad_px) / max(bbox.width, 1)
                                new_font = max(min_font, int(current_font * scale * 0.95))
                                if new_font >= current_font:
                                    new_font = current_font - 1
                                current_font = new_font
                                txt.set_fontsize(current_font)
                                fig.canvas.draw()
                                bbox = txt.get_window_extent(renderer=renderer)
                                attempts += 1

                    except Exception:
                        # If renderer-based sizing fails for any reason, fallback to a readable default
                        txt.set_fontsize(14)

            except (ValueError, IndexError):
                continue

        color_index += 1

    # Styling with larger fonts
    title = _maybe_shape_persian("برنامه هفتگی دروس")

    ax.set_title(title, fontsize=30, fontweight="bold", pad=30, fontproperties=PERSIAN_FONT)

    # Invert y-axis to have Saturday at top (mirror the twin axis as well)
    ax.invert_yaxis()
    try:
        ax2.invert_yaxis()
    except Exception:
        # If ax2 doesn't support invert, reset its limits to match ax
        ax2.set_ylim(ax.get_ylim())

    # Make sure hour tick labels at the top have padding and are large/bold like the day labels
    ax.tick_params(axis='x', pad=12, labelsize=24)
    # Ensure xtick text objects are bold and sized consistently
    for lbl in ax.get_xticklabels():
        lbl.set_rotation(0)
        lbl.set_va('bottom')
        try:
            lbl.set_fontsize(24)
            lbl.set_fontweight('bold')
            lbl.set_fontproperties(PERSIAN_FONT)
        except Exception:
            pass

    # Use explicit subplots_adjust (tight_layout can override manual margins and clip the right labels)
    # For a wider figure give more room on the right for day labels and more plotting space on the left
    fig.subplots_adjust(left=0.04, right=0.86, top=0.94, bottom=0.06)

    # Slightly increase xtick font size to improve readability now that there's more horizontal room
    for lbl in ax.get_xticklabels():
        lbl.set_fontsize(18)

    # Ensure output dir exists
    os.makedirs("generated_charts", exist_ok=True)

    # Generate unique filename
    filename = f"schedule_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join("generated_charts", filename)

    # Save the chart
    plt.savefig(filepath, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()

    return filename


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate_chart")
async def generate_chart(request: Request):
    form_data = await request.form()
    # Keep the raw lessons JSON so we can return it to the template for client-side
    # restoration of the form even if chart generation fails.
    lessons_json = form_data.get("lessons_data", "[]")

    try:
        lessons_data = json.loads(lessons_json)
    except Exception:
        lessons_data = []

    try:
        # Build validated Lesson objects from the parsed data
        lessons: List[Lesson] = []
        for lesson_data in lessons_data:
            schedules = []
            for schedule_data in lesson_data.get("schedules", []):
                schedules.append(LessonSchedule(
                    day=schedule_data["day"],
                    start_time=schedule_data["start_time"],
                    end_time=schedule_data["end_time"]
                ))

            lessons.append(Lesson(
                name=lesson_data.get("name", ""),
                units=int(lesson_data.get("units", 0)),
                schedules=schedules
            ))

        # Generate the chart
        chart_filename = create_schedule_chart(lessons)

        return templates.TemplateResponse("index.html", {
            "request": request,
            "chart_generated": True,
            "chart_filename": chart_filename,
            # Pass the original lessons JSON back so the client can restore form inputs
            "lessons_data": lessons_data
        })

    except Exception as e:
        # On error, include the lessons data so the form can be rehydrated for fixes
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": f"خطا در ایجاد نمودار: {str(e)}",
            "lessons_data": lessons_data
        })


@app.get("/chart/{filename}")
async def get_chart(filename: str):
    """Serve generated chart images"""
    filepath = os.path.join("generated_charts", filename)
    if os.path.exists(filepath):
        return FileResponse(filepath)
    else:
        return {"error": "Chart not found"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)