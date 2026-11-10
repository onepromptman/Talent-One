# Shared profile convention

Harvested from the onepromptman plugins marketplace with two edits: a document theme
(`mode`) is kit-owned, not shared, because it names one kit's design system; the opt-out
example is generic.

Every kit in this marketplace that collects organization facts reads and writes **one**
profile file in the user's working folder: `onepromptman-profile.md`.

The problem this solves: a user who installs three kits should not be asked their
company name three times. The first setup run establishes the shared facts; every later
kit reads them and asks only for what it alone needs.

**Opt-out.** A kit that collects no organization facts at all does not participate and
ships no setup skill (a deliberately generic on-ramp kit where the user brings their own
use case is the standing example; giving it a company dependency would make it worse). Such a kit should still mention in one line that the other kits share a
profile, so the convention is not a surprise later.

## File shape

```markdown
# Profile

researched: 2026-08-26

## Organization
name: Northwind Robotics (confirmed by user)
domain: northwind.example (confirmed by user)
descriptor: builds warehouse automation hardware (web, northwind.example, confirmed by user)
locations: Denver CO; remote US (stated by user)
careers_url: https://northwind.example/careers (web, confirmed by user)
proof_points:
  - Series B, $40M, March 2026 (web, northwind.example/news, confirmed by user)

## Hiring
functions: Software, Mechanical, GTM
levels: mid, senior, staff
volume: roughly 20 hires a year

## Constraints
- Must be authorized to work in the United States without visa sponsorship.
  gate: application | disqualifying: yes

## Brand
voice: plain, warm, concrete
credit: on

## Connectors
ats: greenhouse (connected)
docs: google-drive (connected)

## Kit: talent-one
mode: light
plain_doc: false

## Kit: screen-scribe
enrichment_level: medium
output_target: google-docs

## Kit: talent-alpha
open_role: Senior Backend Engineer
leverage: remote-first, ships in weeks not quarters
```

Everything above `## Kit:` is shared. Everything under a `## Kit:` heading belongs to
exactly one kit and is written only by that kit's setup skill.

## Provenance is mandatory

Every organization fact carries where it came from: `(stated by user)` or
`(web, <domain>, confirmed by user)`. A fact the user never confirmed is either dropped
or tagged `(unverified)`, and any kit that writes candidate-facing text must treat an
unverified fact as an estimate, never assert it.

## Rules for every setup skill

**Read before asking.** On invocation, look for `onepromptman-profile.md` in the working
folder. If it exists, read it and tell the user in one line what you already know.

**Confirm the company, never assume it.** Even with a profile present, ask once whether
this run is for the same organization. People work across an employer, clients, and a
side business, and a wrong guess poisons every downstream artifact. One confirmation
chip is enough; do not re-run the whole interview.

**Ask only what is missing.** Skip any shared section already filled. Ask for your
`## Kit:` block and for shared fields that are genuinely absent.

**Never silently overwrite a shared field.** If your kit needs a different value than
one already recorded, show the conflict and let the user choose.

**Offer a refresh when stale.** If `researched:` is older than 90 days, offer to
re-verify the organization facts. Do not force it.

**Resume, do not restart.** Write `setup_incomplete: <section>` while a run is in
progress and clear it on completion. On the next invocation, resume from that section.

**Every step is skippable and has a safe default.** All kits run on public data alone.
Anything the user supplies makes the output sharper; nothing is a prerequisite.

**Write plain prose to the user.** No YAML, no file paths, no jargon in the
conversation. The profile file is an implementation detail they never have to open.

## Rules for every working skill

Check for the profile before doing work. If it is missing, say this is the first run,
offer setup, and offer to proceed with a one-question minimum instead. Never block.
