# nanibabukokatha

## Overview
"nanibabukokatha" (नानीबाबुको कथा, "children's stories") is a content/production project — not application code — for a planned series of original Nepali-language animated moral/folk stories intended for 2D cinematic animation and YouTube publishing. The repo root contains 50 original Nepali story ideas with titles, summaries, and morals (`nepali_story_ideas.md`), organized into categories (village-life stories, children's moral stories, animal stories, family/emotional stories, magical moral stories). One story — "दूधमा पानी, मनमा ढुङ्गा" (a milkman who waters down milk and unknowingly harms his own son) — has been fully developed into a detailed, segment-by-segment AI video production script (`1.1 दूधमा पानी, मनमा ढुङ्गा/prompt2-dudhma_pani_full_script.md`, 45 segments of ~10 seconds each) plus a master character reference sheet (`prompt3-character.md`) and additional prompt iterations (`prompt4.md`, `prompt4 copy.md`). A `character/` subfolder holds generated character reference images and short video clips (PNG/JPEG portraits and MP4 test clips) supporting that story's production. Root-level `.docx` files (`prompt1.docx`–`prompt4.docx`) appear to be earlier/alternate drafts of the same prompt-development process.

## Domain / Industry
- Domain: Media/content production — AI-generated animated storytelling (Nepali-language moral/folk tales)
- Industry: Media & entertainment / children's content, localized (Nepali) YouTube content production

## URL
- Live/Deployed URL: Not deployed / not specified (no reference to a published YouTube channel or site found in the repo content)
- Repository/Source: `https://github.com/sanamsitoula/nanibabukokatha.git` (found via `git remote -v`)

## How to Start
This is not a runnable software project; there is no build, install, or run process.
1. Review `nepali_story_ideas.md` for the full list of 50 original story concepts.
2. Open `1.1 दूधमा पानी, मनमा ढुङ्गा/prompt3-character.md` for the master visual style and character reference sheet (used to keep every generated video segment visually consistent).
3. Open `1.1 दूधमा पानी, मनमा ढुङ्गा/prompt2-dudhma_pani_full_script.md` for the full 45-segment, scene-by-scene video generation script (each segment includes video prompt, dialogue, voice direction, sound effects, music cues).
4. Reference images/clips for characters live in the `character/` subfolder for use alongside the prompts in an AI video/image generation tool.
5. `prompt1.docx`–`prompt4.docx` in the repo root are earlier Word-format drafts of the prompt-development process and can be opened in any Word-compatible viewer.

## Technology Used
- Languages: Markdown (content/prompts), Nepali (Devanagari script) as the content language
- Frameworks/Libraries: Not applicable — no application code; content is authored for consumption by external AI video/image generation tools (tool not named in-repo)
- Infra/Tools/Services: Git/GitHub for version control (single "Initial commit" on `main`); no build tools, hosting, or app infra

## Key Features
- 50 original, categorized Nepali moral story concepts with title, summary, and moral, explicitly noted as "100% original / copyright-free / 2D-animation-friendly / YouTube-ready"
- Fully developed 45-segment production script for one flagship story ("दूधमा पानी, मनमा ढुङ्गा") with per-segment video prompts, camera plans, dialogue, narration, voice direction, sound effects, and music cues
- Master character reference sheet enforcing strict visual/voice consistency (appearance, clothing, props, voice tone) for each named character across all segments
- Supporting character reference images and test video clips in `character/`
- Story structured as a multi-scene narrative (9+ scenes) with hooks/cliffhangers designed for serialized short-form video release

## Status
In active development — one story ("दूधमा पानी, मनमा ढुङ्गा") is deep into script/prompt production with a nearly-complete 45-segment breakdown and generated reference art/clips, while the remaining 49 story ideas exist only as concept summaries awaiting the same treatment. Version control shows a single "Initial commit" with a connected GitHub remote (`origin/main`), indicating this is treated as an ongoing versioned project rather than a one-off scratch folder.

## Notes
- This folder is essentially identical to the sibling folder "nanibabukokatha - Copy" — a `diff -rq` between the two found no differences in tracked working-tree files (only internal `.git` bookkeeping files, `FETCH_HEAD`/`ORIG_HEAD`, differ). See that folder's own `project_description.md` for details.
- No application/source code was found anywhere in this folder; it is purely a content/prompt-engineering repository for AI-driven animation production.
- Character reference art (`character/*.png`, `.jpeg`, `.mp4`) indicates active use of an external AI image/video generation pipeline, but the specific tool(s) used are not documented in-repo.
