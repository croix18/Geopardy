# Handoff

Project notes for whoever picks this up next, human or Claude session. Read this before changing
anything. The README covers how to play, build and write a unit; this file covers why things are the
way they are, and what has and has not been checked.

## What it is

Geopardy! is a classroom review game for a middle school math room. It looks like a quiz-show board
and runs like a trivia night. It is a review-day game, not a daily tool: it belongs in Deckhand's kit
as a card to open on those days, the way Cadence is. The game was called Boards Up! until 3 Oct 2026
(Croix: "I want to rename as Geopardy!"); "boards up" remains the name of the phase where every team
shows its whiteboard. The title is editable on the setup screen, and a device that saved the old
default title is moved to the new one at load.

## Where it runs (hard constraints)

- On the classroom Promethean panel's own browser (a Chromebox running Chrome), not a mirrored laptop.
- Opened as a file from Google Drive over `file://`. The district filter blocks `github.io`, so a
  Pages copy never reaches the panel.
- So every game is **one self-contained HTML file with no network requests**: fonts, KaTeX, the music
  and the unit are all embedded. Do not add a CDN link, a web font link or a fetch.
- It must also work on a phone in portrait, because that is where builds get previewed.
- No student names or student data, ever. Teams are named at the setup screen and live only in the
  browser's local storage.

## Design rules (decided, do not relitigate without asking)

- Every team answers every question. Nobody buzzes in.
- Scoring only adds. There is no penalty for a wrong answer. The score adjuster on the board is for
  fixing a mis-tap, and the game says so.
- Points, not money. Questions get harder as the points rise, and the point value has to match the
  difficulty, across categories as well as down each one.
- Each category is a ladder: tiles open lowest first.
- One-day games only. A full board is allowed to be longer than a period; the bell guard ends it.
- Quiz-show colors and type (deep blue, gold, condensed display face). This tool deliberately does not
  use the navy, gold and cream house style of the other classroom tools.
- Real math typesetting everywhere a student reads math.
- Music is real public-domain Mozart recordings. A fully synthesized theme was tried and rejected as
  raspy; only the short stings are synthesized.
- Units are written by script and checked by machine. The JSON is hand-editable for small tweaks.

## How the engine works

`tools/build.py` replaces the markers in `engine/index.html` and writes one file per unit to `games/`.

- **Screens** (`game.js`): setup, board, question, podium, plus overlays (menu, bell guard, resume,
  score adjust, Double Up splash). Everything renders from one state object `S` into `#app`.
- **A question's phases**: `read` -> `solo` -> `huddle` -> `boards` -> `answer`. Solo time is
  30/45/60/75/90 s by tier, times the setup multiplier, rounded to 5 s. Huddle is 20 or 30 s. The Final
  is worth double the top tier, with `final.solo` seconds of solo time (default 60) and a 30 s huddle.
- **Timer and music** share the audio clock, so the countdown and the cue cannot drift. Each Mozart cue
  is started part-way through so its last chord lands on zero. Solo plays K. 545, the huddle plays the
  Symphony 40 finale, and the Final's huddle plays the menuetto.
- **Stings** (pick, huddle, boards, correct, not yet, Double Up, winner) are rendered once at start in a
  worker built from the text of `quizmusic.js`. That is why its script tag must keep `id="engine"`.
- **Bell guard**: `schedule.json` is the school's bell schedule copied from Deckhand, with teal and
  black weeks and Wednesday bells. The setup screen finds the current period, fills in the end time,
  and estimates how many questions fit (solo + huddle + 50 s each). In the game, with six minutes left,
  it offers the Final.
- **Saving**: the game in progress is saved to local storage under a key that includes the unit title
  and board size, so one unit's save is never offered on another unit's board. Preferences (team
  count, names, volume, timing) are shared across units.
- **Keys**: space presses the main button, `U` undoes, `P` pauses.
- **Figures**: a question may carry `fig` and `afig` (inline SVG). On the answer screen the figure sits
  beside the answer. Figure styling is by class: `fs` shape, `fd` dashed line, `fm` marks and
  dimension lines, `fu` unknown, `fa` area labels. Print restyles them black on white.
- **Fit**: if a question plus its answer is taller than the space between the header and the buttons,
  `fitQuestion()` scales the block down. It reruns on resize and when fonts finish loading.

## History

- **Start**: `Boards_Up_Review_Game.html` (the game's name then), a working single-file build with a 4 x 4 placeholder unit.
- **2 Oct 2026**: first two real units, and the engine changes they needed:
  - board rows shrink and tile numbers scale so a 5-row board fits above the score strip;
  - the question block scales to fit, and display-math spacing tightens on the answer screen;
  - saves are keyed per unit;
  - `final.solo` sets the Final's solo time;
  - printing waits for every embedded font (the answer key printed blank math from the setup screen),
    key rows no longer split across pages, long category names wrap, and a recording sheet's last
    page with one category prints as a single column;
  - figures (`fig`, `afig`) on the question screen, the answer screen and the printed key;
  - on a portrait screen the category font shrinks to fit the longest word.
- **3 Oct 2026**: the single file was split into `engine/` parts and this repository was set up. The
  split is lossless: building from the parts reproduces the delivered game byte for byte.
- **3 Oct 2026, later**: renamed Geopardy! — default title, `<title>`, built file names
  (`games/Geopardy_*.html`), docs. Storage keys were already name-free (`reviewgame.*`), so saved
  games and preferences carry over; only a saved default title is rewritten.
- **Planned (agreed with Croix, 3 Oct)**: Cadence gets an "Export a Geopardy board" mode — five
  benchmarks, a ladder drawn from its generators (standard rigor low, high rigor at the top), verified
  by its own pipeline, written as a unit file this engine consumes (`CTEX.toTeX` for the math). The
  Windy Hill lesson banks can emit the same file. Geopardy stays a static single file; the generating
  and checking happen in Cadence. A Deckhand card for Geopardy mirrors the Cadence card.

- **4 Oct 2026**: two units for the on-level course, asked for by Croix as one of the "family
  hooks" when M7 moved onto the shared build kit: **Circles** (`units/src/circles.py`; M7 lessons
  4.05–4.10 — `area_of_polygons` already covers 4.01–4.04, so the two games together are the Unit 4
  review) and **Samples & Scale** (`units/src/samples_and_scale.py`; M7 Unit 5). `figs.py` gained
  `circle`, `sector`, `seg` and `dot` (a radius or diameter is labelled on a drawn segment, so its
  `check=` holds it to the circle; a shaded sector is compared with the angle actually drawn); the
  area unit regenerates byte for byte. Both generators compute every answer from the question's own
  numbers with exact fractions, print the answer and the worked step from the computed value, compare
  it with a value worked by hand, and refuse to write a unit in which two questions share an answer.
  **Transfer surfaces are kept out by the generator**: the game is played on the review day, before
  the unit test, and the test's two transfer items (HOUSE STYLE ruling 18) must meet a surface nobody
  rehearsed — for Unit 4 a bicycle wheel's distance and a walkway by subtraction, for Unit 5 a sample
  fraction given as a decimal and a model at 1 : N converted to centimeters. A question that names
  one of those stops the build. If a unit's transfer items change, change the guard at the end of
  its generator. Questions are original, in the lessons' own wording ("Use 3.14 for π", "Predict",
  "scale factor"); the probability questions say "use these results", so 27 heads in 60 flips is not
  an invitation to answer one half.

## What is verified, and what is not

Verified by `tools/check.sh`, in headless Chromium:
- every unit answer (computer algebra for exponents; shoelace area from drawn coordinates for area;
  exact fractions against a second, hand-worked value for circles and for samples and scale),
  and every labelled length against the segment it labels;
- a full game per unit: all 25 tiles in ladder order, a mid-game reload and resume, the Final and the
  podium, with no console errors and no question overlapping the header, clock or buttons;
- the same at 1920 x 940, 1366 x 768, 1280 x 1024 and a phone in portrait;
- the recording sheet and answer key render to PDF with math and figures.

Not verified by any test:
- how the music and stings sound, or whether the cues land on zero by ear;
- a real print dialog on a real printer;
- the panel itself. The checks run in desktop Chromium, not on the Chromebox.

## Open questions

- **Game length.** With the solo, huddle and boards-up flow, about 18 or 19 of 25 questions fit in
  45 minutes. The ladder means the unplayed tiles are the top of some categories. Starting the ladder
  at 200 (setup screen) trades the warm-up row for harder tiles.
- **Rhombus tiles.** In Area of Polygons, the 300 and 400 rhombus tiles give the two diagonals. They
  can be solved with half the product of the diagonals or by splitting into two triangles. If a class
  has only seen base times height, swap them.
- **Work-backward tiles.** Three 500-level area tiles ask for a missing measurement from a given area.
  They need only fact-family reasoning, but they go past "find the area".

## Pushing from a Claude session

A session's own GitHub connection only covers the repositories attached to it. This repository is
pushed with a fine-grained personal access token instead (this repository only, Contents: read and
write), sent as a Basic auth header on each git command:

1. Put the token in `.github-token` at the repository root and `chmod 600` it. It is git-ignored.
   Never put it in the remote URL, a commit message or any output.
2. Run `tools/push.sh "message"`. It commits as the GitHub no-reply address (a gmail author is
   rejected by email privacy), pushes, then compares the remote head with the local head and fails
   loudly if they differ. Set `CLAUDE_MODEL_NAME` and `CLAUDE_SESSION_URL` for the commit trailers.
3. If a push fails, `curl -s -o /dev/null -w "%{http_code}\n" -u "x-access-token:$T"
   "https://github.com/croix18/Geopardy.git/info/refs?service=git-receive-pack"` returns 200 when the
   token can push and 401 when it cannot.

The GitHub API is not available from a session, so no releases or repository settings from here.
Rotate the token if it was ever pasted into a chat.

## House rules for changes

- Change engine parts, never a built game. Rebuild, run `tools/check.sh`, then look at the screenshots
  in `out/`: the script catches overlaps and errors, not ugliness.
- Vendor files and audio are included verbatim. Do not reformat them.
- Built games are tracked so they can be downloaded from GitHub. Rebuild them in the same commit as the
  source change that affects them.
- Keep this file current. It is the project's memory.

## Windmill and the room (3 Oct 2026)

Croix's tools now coordinate through **Windmill** (`croix18/Windmill`): the spine (the year's plan as one
JSON — every school day, both courses, lesson, benchmarks, IXL due dates, the bell and week colour from
Deckhand's own schedule), the **room** (one small object the tools exchange: `plan` · `tally` · `panel` ·
`roster` · `log`, one owner per part, newest copy per part, data tiers so counts ride every road, first
names ride Drive or encrypted, and grades never leave Tally), the reader every tool embeds, two room-code
forms, and a conformance test each repo runs. The design — alternatives, the contract, three transports
(room code · Drive file · Apps Script), per-tool changes, the spiral rule, the build order — is the
*Room Coordination Plan*, a Claude doc of Croix's: https://claude.ai/code/artifact/9db84d04-9444-48c4-adad-9c68905eefd8 (open it with the docs tool). Croix's standing
instruction: "Keep it over engineered. I want everything." Read Windmill's `README.md` and `HANDOFF.md`
before building this tool's part.

**Geopardy's part.** The setup screen will offer a ladder from the room: categories = the unit's five
weakest benchmarks, tiers by `atGoal` ascending, items from Cadence's export; after the podium it writes
`panel.geopardy[]` (share of teams right per tile) for the heat map. `engine/schedule.json` is a copy of
Deckhand's bell block; Windmill's spine carries the same block and can replace the copy at build.
