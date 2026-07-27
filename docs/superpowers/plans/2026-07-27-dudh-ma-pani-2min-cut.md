# दूधमा पानी, मनमा ढुङ्गा — 2-Minute Cut Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and render a ~2-minute condensed cut of "दूधमा पानी, मनमा ढुङ्गा" in DaVinci Resolve, using one representative shot per scene from the existing 46-clip footage set.

**Architecture:** Use the `davinci-resolve` MCP tools to drive Resolve directly: create a project, import 12 hand-picked clips (one per scene) into the Media Pool, assemble them on a timeline in scene order with a title card and a moral-text end card, then render to the project's designated output folder. No source media is modified — only referenced.

**Tech Stack:** DaVinci Resolve (via `mcp__davinci-resolve__*` tools), ffmpeg (for pre-import frame extraction/inspection only, source-safe read).

## Global Constraints

- Never modify, transcode, relink, or replace any file under `1.1 dudh ma pani/video/` — reference clips into the Media Pool only.
- Timeline format must match source: 1280×720, 24fps.
- Final render goes to `1.1 dudh ma pani/video_davi/`.
- Exactly one shot per scene, 12 scenes total (Scene 1 → Scene 12), hard cuts only.
- No music/SFX, no subtitles, no color grading in this pass.
- Title card at open (story title), moral-text card at close (Scene 12's `FINAL MORAL` line).

---

### Task 1: Select the 12 representative shots

**Files:**
- Create: `1.1 dudh ma pani/shot-selection.md`

**Interfaces:**
- Produces: a table of `Scene -> chosen filename -> one-line reason`, used verbatim by Task 4 (import) and Task 5 (timeline assembly order).

- [ ] **Step 1: Extract a mid-clip still frame for every candidate shot**

For each of the 46 files in `1.1 dudh ma pani/video/`, extract the frame at the clip's midpoint to a scratch dir for visual review:

```bash
mkdir -p /tmp/shot-review
cd "D:/claude_project/nanibabukokatha/1.1 dudh ma pani/video"
for f in *.mp4; do
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
  mid=$(python3 -c "print(float('$dur')/2)")
  ffmpeg -y -ss "$mid" -i "$f" -frames:v 1 "/tmp/shot-review/${f%.mp4}.jpg" -loglevel error
done
```

- [ ] **Step 2: Review frames against the script and pick one shot per scene**

Read `1.1 dudh ma pani/prompt2-dudhma_pani_full_script.md` scene-by-scene. For each scene, view the extracted stills for its candidate shots (`Read` tool on the jpgs) and pick the one whose framing/action best matches that scene's Dialogue + Animation Direction + Scene Ending Hook (the emotional peak or cliffhanger). Note the filename and a one-line reason.

- [ ] **Step 3: Write the selection table**

```markdown
# Shot Selection — दूधमा पानी, मनमा ढुङ्गा 2-min cut

| Scene | Chosen file | Reason |
|-------|-------------|--------|
| 1 | S1S?.mp4 | ... |
| 2 | S2S?.mp4 | ... |
| ... | ... | ... |
| 12 | S12S?.mp4 | ... |
```

Fill in all 12 rows with the actual chosen filenames from Step 2.

- [ ] **Step 4: Verify the table**

Confirm the table has exactly 12 rows, scenes 1–12 in order, each filename exists in `1.1 dudh ma pani/video/`, and no filename is reused across two scenes.

- [ ] **Step 5: Commit**

```bash
cd "D:/claude_project/nanibabukokatha"
git add "1.1 dudh ma pani/shot-selection.md"
git commit -m "Select representative shots for 2-min condensed cut"
```

---

### Task 2: Create the Resolve project with matching timeline settings

**Files:** none (Resolve project state only)

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: a current, open Resolve project named `dudh-ma-pani-2min` with timeline resolution 1280×720 and frame rate 24, used by every subsequent task.

- [ ] **Step 1: Ensure Resolve is running and connected**

Call `mcp__davinci-resolve__resolve_control(action="launch")`, then `mcp__davinci-resolve__resolve_control(action="get_version")`.
Expected: a version string is returned (no "Not connected" error).

- [ ] **Step 2: Create the project**

Call `mcp__davinci-resolve__project_manager(action="safe_project_create", params={"name": "dudh-ma-pani-2min", "dry_run": false})`.
Expected: `{success: true, name: "dudh-ma-pani-2min"}`.

- [ ] **Step 3: Confirm it's the current project**

Call `mcp__davinci-resolve__project_manager(action="get_current")`.
Expected: `{name: "dudh-ma-pani-2min", ...}`.

- [ ] **Step 4: Inspect available setting keys**

Call `mcp__davinci-resolve__project_settings(action="get_setting")` (no `name`, returns all settings). Locate the exact keys for timeline width, timeline height, and timeline frame rate (typically `timelineResolutionWidth`, `timelineResolutionHeight`, `timelineFrameRate`).

- [ ] **Step 5: Set timeline format to match source**

Call `mcp__davinci-resolve__project_manager(action="safe_set_project_settings", params={"settings": {"timelineResolutionWidth": "1280", "timelineResolutionHeight": "720", "timelineFrameRate": "24"}})` (adjust key names to whatever Step 4 revealed).
Expected: `{success: true}`.

- [ ] **Step 6: Verify**

Re-run `mcp__davinci-resolve__project_settings(action="get_setting")` and confirm the three values now read 1280 / 720 / 24.

---

### Task 3: Import the 12 selected clips into the Media Pool

**Files:** none (Resolve Media Pool state only)

**Interfaces:**
- Consumes: `1.1 dudh ma pani/shot-selection.md` from Task 1 (the 12 chosen filenames), the open project from Task 2.
- Produces: 12 media pool clip entries, used by Task 4's `create_timeline_from_clips`.

- [ ] **Step 1: Import the 12 files**

Call `mcp__davinci-resolve__media_storage(action="import_to_pool", params={"items": [<12 absolute paths from shot-selection.md, in Scene 1→12 order>]}})`.
Expected: `{imported: [...12 entries...]}`.

- [ ] **Step 2: Verify count and order**

Call `mcp__davinci-resolve__media_pool(action="get_current_folder")` then list its clips (or use `project_settings(action="project_summary", params={"include_clips": true})`). Confirm exactly 12 clips are present and each filename matches a row in `shot-selection.md`.

---

### Task 4: Assemble the timeline in scene order

**Files:** none (Resolve Timeline state only)

**Interfaces:**
- Consumes: the 12 media pool clip IDs from Task 3, in Scene 1→12 order.
- Produces: a timeline named `dudh-ma-pani-2min` with 12 video/audio clips back-to-back, used by Task 5 (title/end cards) and Task 6 (render).

- [ ] **Step 1: Create the timeline from the ordered clip list**

Call `mcp__davinci-resolve__media_pool(action="create_timeline_from_clips", params={"name": "dudh-ma-pani-2min", "clip_ids": [<12 clip IDs from Task 3, Scene 1->12 order>], "if_exists": "fail"})`.
Expected: `{success: true, name: "dudh-ma-pani-2min", id: ...}`.

- [ ] **Step 2: Verify timeline duration and clip count**

Call `mcp__davinci-resolve__timeline(action="get_current")` to confirm it's active, then check total item count on video track 1 (e.g. via `timeline_item(action="get_name", params={"track_type": "video", "track_index": 1, "item_index": 0})` through `item_index: 11`, expecting all 12 to resolve without error). Confirm `end_frame - start_frame` corresponds to ~120 seconds at 24fps (~2880 frames, allowing for the one 8s clip).

---

### Task 5: Add the title card and moral end card

**Files:** none (Resolve Timeline state only)

**Interfaces:**
- Consumes: the assembled 12-clip timeline from Task 4.
- Produces: a 14-item video track 1 (title card + 12 scene clips + end card), used by Task 6 (render).

- [ ] **Step 1: Discover the exact title-insertion action name**

Call `mcp__davinci-resolve__timeline(action="list")` to confirm the timeline tool responds, then attempt `mcp__davinci-resolve__timeline(action="insert_title_into_timeline", params={"title_name": "Text", "position": "start"})` against a scratch/test scenario first if unsure of parameter names — if it errors with an unknown-action message, use the error's suggestion or the Resolve scripting reference (`docs/reference/resolve_scripting_api.txt` in the davinci-resolve MCP repo) to find the correct action (Resolve's native API method is `Timeline.InsertTitleIntoTimeline`).

- [ ] **Step 2: Insert the title card at the timeline start**

Using the confirmed action, insert a standard "Text" title generator positioned before the first scene clip (frame 0). Set its text to the story title: "दूधमा पानी, मनमा ढुङ्गा". Set its duration to 2.5 seconds (60 frames at 24fps) via `timeline_item(action="set_property", params={"key": "Duration", "value": 60, "track_type": "video", "track_index": 1, "item_index": 0})` (adjust key name if `get_property` shows a different one).

- [ ] **Step 3: Insert the end card after the last scene clip**

Insert a second "Text" title generator immediately after the Scene 12 clip. Set its text to the `FINAL MORAL` line from `prompt2-dudhma_pani_full_script.md`:
"बेइमानीले कमाएको धन खोलाको पानीजस्तै बगेर जान्छ, तर इमानले कमाएको विश्वास दूधजस्तै जीवनभर शक्ति दिन्छ। जुन हातले अरूलाई धोका दिन्छ, त्यही धोका एक दिन आफ्नै घरको ढोका ढक्ढक्याउन आइपुग्छ।"
Set its duration to 5 seconds (120 frames at 24fps).

- [ ] **Step 4: Verify final track structure**

Call `timeline_item(action="get_name", ...)` for `item_index` 0 through 13 on video track 1. Expected: index 0 = title card, indices 1–12 = the 12 scene clips in order, index 13 = end card.

---

### Task 6: Render to `video_davi`

**Files:**
- Output: `1.1 dudh ma pani/video_davi/dudh-ma-pani-2min.mp4`

**Interfaces:**
- Consumes: the finished 14-item timeline from Task 5.
- Produces: the final rendered mp4 deliverable.

- [ ] **Step 1: Set render format/codec to match source**

Call `mcp__davinci-resolve__render(action="set_format_and_codec", params={"format": "mp4", "codec": "H.264"})`.
Expected: `{success: true}`.

- [ ] **Step 2: Prepare the render job targeting video_davi**

Call `mcp__davinci-resolve__render(action="prepare_render_job", params={"target_dir": "D:/claude_project/nanibabukokatha/1.1 dudh ma pani/video_davi", "custom_name": "dudh-ma-pani-2min", "dry_run": false})`.
Expected: `{success: true, job_id: ...}`.

- [ ] **Step 3: Start the render and wait for completion**

Call `mcp__davinci-resolve__render(action="start", params={"job_ids": [<job_id>]})`, then poll `mcp__davinci-resolve__render(action="get_job_status", params={"job_id": <job_id>})` until status is complete (not `is_rendering`).

- [ ] **Step 4: Verify the output file**

Run `ffprobe -v error -show_entries format=duration -of csv=p=0 "D:/claude_project/nanibabukokatha/1.1 dudh ma pani/video_davi/dudh-ma-pani-2min.mp4"`.
Expected: file exists, duration is between 120 and 135 seconds, video stream is 1280×720.

- [ ] **Step 5: Save the project**

Call `mcp__davinci-resolve__project_manager(action="save")`.
Expected: `{success: true}`.
