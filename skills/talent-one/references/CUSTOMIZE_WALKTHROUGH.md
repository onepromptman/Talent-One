# Customizing the documents: the walkthrough

Loaded on demand by `talent-one-setup` step 8: after a run, or when the user asks for
help making the documents their own ("help me customize my JD", "review my documents",
"make these ready to use"). It walks a recruiter who is not technical through each
document before it reaches a candidate, a hiring manager or an interviewer. You never
write artifact content yourself and never edit rendered HTML: every change goes through
update mode (section 4).

## Why this step exists

Say it once, in one or two plain sentences, before the first document: every document is
a complete first draft, not a finished one. The kit drafts from public data and the
profile, so it cannot know the approved pay band, the team's real interview stages, the
proof points the company is happy to share, or the benefits and legal wording the company
already uses. The job description, interview plan, outreach campaign and interviewer
briefing need the most work; every other document needs at least a quick check.

## 1. Find what to review

- **Which role.** The role homes under `talent-one-roles/` (legacy `talent-one-runs/`
  folders too). One role: use it and say which. Several: ask with one chip question,
  most recent first.
- **Which documents.** The newest run folder's rendered `NN_*.html` files and their
  `content/NN.content.json` (the role home's `content/` cache when the run folder has
  none). If the user named one ("my JD"), start there and offer the rest after. Otherwise
  propose this order and let them skip any: 02 job description, 06 interview plan,
  05 outreach campaign, 09 interviewer briefing, then 07 calibration brief, 08 screen
  guide, 04 sourcing playbook, 03 talent map, 01 educational brief.
- **Skip what is done.** `talent-one-roles/<role_slug>/ROLE.md` records documents already
  reviewed (section 6). Offer to skip those unless the document was regenerated since.
- **Build the checklist from the files, never from memory.** For each document read its
  content JSON, the pack, and the profile, and collect:
  1. every figure that is not the company's own: a `{"pill": "Estimate", ...}` object,
     prose that labels a number an Estimate, and in the sourcing playbook every rate
     labelled Benchmark or ORACLE (public benchmark rates) rather than HOUSE (the
     company's own hiring data). The interview plan, interviewer briefing, screen guide
     and educational brief usually carry no figures; their checks are company and
     process facts;
  2. every company fact: anything drawn from the profile's `## Organization` (name,
     description, locations, proof points), benefits and EEO text, and any line the
     profile tags `(unverified)`, which goes first;
  3. the pay: the pack's canonical range and every place a document quotes it;
  4. assumptions: `handoff.assumptions`, the pack's assumptions and caveats, and any
     waiver recorded at the ask-first gate;
  5. fill-ins: bracketed merge fields such as `[[FirstName]]` in outreach copy and the
     sourcing playbook, which the user fills per candidate or once per search before
     sending.

## 2. Confirm the shared facts once, up front

Several documents repeat the same facts, so confirm them once before going document by
document and never ask twice:

- the company name, its one-line description, and the proof points (news, milestones,
  numbers) the job description and outreach use;
- the pay range, and whether it is approved to post;
- the interview stages: how many, in what order, how long, and who runs each (the
  interview plan, screen guide and interviewer briefing all quote them);
- the hiring manager's and recruiter's names, where the documents use them;
- eligibility lines, shown exactly as the profile holds them, only if it has any.

Use AskUserQuestion, at most four items per pass, each with the same three answers:
"Right as written", "Change it", "Skip for now". A "Change it" gets one plain follow-up
message asking for the right wording.

## 3. Then one document at a time

For each document, one short message in plain words, then the questions:

1. What it is for and who reads it, in one line.
2. "Check these before you use it": the per-document items at the end of this file plus
   every item section 1 found in it, named the way the page shows them (the section
   heading, the figure as written). Never show content keys, slot names, JSON or file
   paths; the user only ever sees the document.
3. Ask at most four items per pass, with the same three answers; group long lists.
4. Close the document with one of: "Ready to use", "Ready once you make the changes we
   noted", or "Updating it now" (changes queued for section 4). Move on, or stop when the
   user says so; the walkthrough can resume later from `ROLE.md`.

## 4. Applying a change

There is one change path, update mode in `references/ORCHESTRATOR_UPDATE_MODE.md`. Decide
here what changes; apply it there.

- **A wrong company fact.** Fix that line of the profile first, tagged `(stated by user)`,
  then run update mode for every document that quoted the old wording.
- **A pack fact** (the pay range, a requirement, the stages, a target): update mode (a).
  It updates the pack with provenance and searches every cached document for the old
  value, so one answer fixes every document that repeats it.
- **One document only** (a sentence, a heading, a section to drop): update mode (b), or
  the owning agent in update mode when the change touches dependent prose.
- Batch the changes from one document, or from the shared-facts pass, into one update.
  Re-render, re-verify, deliver the new file with update_artifact, and tell the user in
  one line what changed and where. A re-render takes seconds once the content is patched.
- Never hand-edit the HTML and never ask the user to. If they would rather finish the
  wording themselves in Word or their ATS, that is fine for the final copy; say in one
  line that such edits do not flow back, and the next update re-renders from the kit's
  own copy.

## 5. Honesty rules while confirming

- "Looks right" does not turn an Estimate into Sourced. It stays an Estimate; the user
  only decides whether to keep it, replace it, or drop it.
- These follow the pack's seed floor (`CONTEXT_PACK.md` section 2). A figure the user
  states in chat (the approved band, their real reply rates) is an Estimate with method
  `recruiter-stated`. It is Internal only when it comes as an export from the company's
  own system of record (an ATS report, an approved comp band document), and Sourced only
  from a named, dated document cited by name and date.
- Eligibility lines and the equal opportunity statement stay exactly as the user wrote
  them. Never draft or soften them; a change comes from the user word for word, with
  counsel review recommended.
- A fact the user cannot confirm is dropped or stays an Estimate, never kept as a stated
  fact. "TBD" and placeholder prose are never the answer; an omitted section is.

## 6. Record it

Append one line per document walked to `talent-one-roles/<role_slug>/ROLE.md`: date,
document, "reviewed" or "reviewed, changes applied", and what changed. Earlier lines stay
as they are. A document regenerated after its review counts as not reviewed until the
user walks it again.

## Per-document checks

Add these to the checklist for each document; skip any the run left out.

### 02 Job description (needs the most work)
- The title and level: the title the company actually uses.
- The line under the title: location, work model, and the pay range as approved to post.
- Responsibilities and requirements: the hiring manager agrees with each one, and no
  nice-to-have is listed as a must.
- The opening and closing paragraphs: the company description and proof points are true
  and current.
- The benefits paragraph: the company's own benefits summary.
- The equal opportunity statement: the company's own text, word for word.
- The notes beside the posting and "what we changed from intake": these are for the
  recruiter, not the posting. Confirm each change the kit made to the intake draft.
- The pay comparison: market figures are Sourced or Estimate as marked; the posted range
  is the company's own decision.

### 06 Interview plan (needs the most work)
- The stages: number, order, length, and who runs each match the real process.
- Each skill being tested has one owner: the actual interviewer or role.
- Every question and its strong and weak answer guide: the hiring manager reads each one
  and replaces any that do not fit the team's work.
- The hard no's: agree on them with the hiring manager before the first interview.
- Any skill a Caution box says no stage covers.

### 05 Outreach campaign (needs the most work)
- Every proof point, number and claim about the company or team: true, current, and
  cleared to share with candidates.
- The bracketed fill-ins: know what goes into each before anything is sent.
- The sender, tone and sign-off sound like the person sending.
- Open and reply rate targets come from public benchmarks unless the user's own numbers
  replace them.
- The texting rule and any compliance line stay as written unless the company's legal
  team says otherwise.
- The send days and gaps fit the user's sending tool.

### 09 Interviewer briefing (needs the most work)
- The stages and owners match the interview plan confirmed above.
- Each interviewer's card goes to the right person, with the right focus.
- The debrief form fields and the decision meeting agenda match how the team decides.
- The prep time is realistic for these interviewers.

### 07 Hiring-manager calibration brief
- Market and pay figures: each is Sourced or Estimate as marked.
- The requirement calibration and trade-offs are proposals for the meeting, not
  decisions already made.
- The response times promised by recruiter and hiring manager: set them with the manager.

### 08 Recruiter screen guide
- The pay, location and logistics questions match the approved range and any
  eligibility lines.
- The spot-check answer keys: the hiring manager glances at the expected answers.
- The sixty-second pitch: every company fact is true and current.

### 04 Sourcing playbook
- Channel yields and the pipeline math (how many contacts, screens and onsites one hire
  takes): rates marked Benchmark or ORACLE are public benchmarks, planning numbers only,
  until the company's own hiring data replaces them (marked HOUSE).
- Search strings: run one in the user's own search tool and adjust if the results are off;
  fill any bracketed field first.
- The weekly timeline: the hiring manager has agreed to their side of it.

### 03 Talent map
- Company lists: remove any the user will not recruit from (partners, customers, a
  no-hire agreement).
- Pool sizes and pay by level: Sourced or Estimate as marked; Estimates are for planning.
- Locations: match where the company can actually hire.

### 01 Educational brief
- For the recruiter only, never sent out, so it rarely needs changes. Check that the team
  and product description matches what the hiring manager said.
