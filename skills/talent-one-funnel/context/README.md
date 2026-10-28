# context/: set up the desk

These files let the Oracle brief itself. Copy each `*.example.md`, drop the `.example`
from the name, fill it with your real situation, and either keep it in your working
folder (the `talent-one-funnel` skill reads `context/*.md` there when present) or upload
it to your Claude Project's knowledge for the paste-in edition.

| File | What it is |
|---|---|
| `competitor-watchlist.example.md` | Who you actually win and lose candidates against |
| `sourcing-posture.example.md` | Your stance, constraints and non-negotiables |

A perfect prompt on an empty desk gets a mediocre answer; these files are the desk.

**Privacy:** keep real competitor strategy and real funnel data private. The
`.gitignore` in this folder ignores every `*.md` here except the `*.example.md`
templates and this README, so a filled-in copy is not committed by accident.
