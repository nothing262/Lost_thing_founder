# Campus Lost and Found Matcher (DAA Project 5)

RGUKT Ongole — Design and Analysis of Algorithms project

## Overview
A local browser application that records fictional Lost/Found item reports, searches reports by category or description keyword, suggests opposite-kind matches with a transparent score, and tracks report statuses.

**Safety/privacy scope:** use fictional sample records only. Do not enter personal contact details. A match score is only a suggestion and does not prove ownership.

## Files
- `app.py` — complete standalone Python application; no external packages or shared `common.py` required.
- `data.json` — persistent JSON store. It begins empty; reports are added through the app.

## Requirements
- Python 3.10+ (uses only the Python standard library)
- Any modern browser

## Run
1. Extract the project folder.
2. Open a terminal/Command Prompt inside `05_lost_found`.
3. Run:
   - Windows: `py app.py` (or `python app.py`)
   - macOS/Linux: `python3 app.py`
4. Open the URL printed by the terminal, normally `http://127.0.0.1:8000`.
5. Keep the terminal open while using the app. Press `Ctrl+C` to stop.

If port 8000 is already occupied:
- Windows CMD: `set PORT=8001` then `py app.py`
- PowerShell: `$env:PORT="8001"; py app.py`
- macOS/Linux: `PORT=8001 python3 app.py`

## How the match score works
Candidates are considered only if:
- one report is Lost and the other is Found,
- categories match (case-insensitive),
- the candidate is not already Returned.

Score:
- Same category: +3
- Each distinct shared description word: +1
- Same location (case-insensitive): +2
- Dates within 3 days: +1

Candidates are sorted by score descending, then report ID ascending. Reasons are displayed with each candidate. Description words are treated as a set, so repetitions do not add repeated points.

## Usage / sample walkthrough
1. Add a Lost report: Category `Bottle`, Description `Blue steel bottle`, Location `Library`, date `2026-10-08` (use any valid date). It receives an ID.
2. Add a Found report with the same details, selecting `Found`.
3. Use the first report ID in **Suggest matches**. The candidate receives score 9: category 3 + shared words blue/steel/bottle 3 + same location 2 + dates within 3 days 1.
4. Search keyword `bottle`; both reports should appear in results.
5. Update status manually as appropriate.

## Extension implemented: linked verified pair
The extension links a Lost report with a Found report:
- Use **Link verified Lost + Found pair** with the Lost ID first and Found ID second.
- Both records are marked `Matched` and store each other's `linked_id`.
- Marking either linked record `Returned` automatically marks its partner `Returned`.
- Linking requires valid IDs, Lost/Found kinds, and matching categories.

## Tests (6 documented cases)
| # | Input/action | Expected result |
|---|---|---|
| 1 | Add Lost and Found reports with same category, description, location and dates within 3 days | Suggestion score 9, with reasons shown |
| 2 | Two Lost reports of the same category | They are not candidates for each other |
| 3 | Lost `Bottle` and Found `Laptop` | No candidate due to category mismatch |
| 4 | Dates 5 days apart, with same category/description/location | No nearby-date point; score is 8 |
| 5 | Mark a candidate Returned then run match search | Returned report is omitted as a candidate |
| 6 | Match using an unknown report ID | Readable error: report ID does not exist |
| 7 | Link a valid Lost and Found pair, then mark one Returned | Both reports are marked Returned |
| 8 | Add blank category/description/location or invalid date | Input is rejected with a readable message |

Record actual results when you execute the tests for your submission.

## Design summary
- `load_data()` reads JSON records from disk.
- `save_data()` writes a temporary file then replaces `data.json`.
- `matches()` filters candidates and computes score/reasons.
- `handle()` processes add/search/match/status/link actions.
- `page()` renders the forms and reports table.
- A local `HTTPServer` serves the interface on `127.0.0.1` only.

## Limitations
- Prototype for local, single-operator classroom use; not a hosted campus-wide service or authentication system.
- Manual report status and ownership checks are expected.
- Category equality is required; common words can cause weak suggestions.
- Uses fictional records and does not collect claimant contact details.
