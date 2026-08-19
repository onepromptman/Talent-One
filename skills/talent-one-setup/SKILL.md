---
name: talent-one-setup
description: >
  Guided first-run setup for the Talent One recruiting kit. Use when the user
  says "set up talent one", "talent one setup", "configure talent one",
  "personalize talent one", or when any talent-one skill finds no
  talent-one-profile.md and the user opts into setup. Researches the user's
  company automatically, then captures roles, constraints, tools, and branding
  in a short guided conversation and writes the profile. No files for the user
  to edit, every step skippable.
---

# Talent One — setup wizard

Produce `talent-one-profile.md` in the working folder through a guided conversation. The user should never see YAML, file paths, or jargon. Every question has a safe default and can be skipped. If a partial profile exists (a `setup_incomplete` marker in the file), resume from the first missing section instead of restarting.

## 1. Welcome

One short message: what Talent One makes (the eight artifacts, one line each, listed in execution order: HM calibration brief, educational brief, talent map, JD, interview plan, screen guide, sourcing playbook, outreach campaign; run order is handled automatically), that setup takes about 5 minutes, and the two paths: full setup now, or skip and build one artifact immediately (route to the requested talent-one-* skill; setup can happen later).

## 2. Company (HARD GATE: always ask, never assume)

**Non-negotiable rules for this step:**

1. **ALWAYS ask which company this profile is for, with AskUserQuestion, even when you think you know.** Chat history, Claude memory, project context, the user's email domain, and prior sessions are NOT valid sources for the company identity. Users often work across several companies (their employer, clients, a side business); guessing picks the wrong one and every artifact inherits the error. If context suggests candidates, offer them as options in the question ("Acme Inc / another company"), but the user must pick. Never skip the question.
2. **Confirm identity before researching.** Ask for the company name AND website URL in the same question (the URL is not optional: common-word company names collide with unrelated companies in search). If the name is ambiguous, show the candidates you find and have them pick. Do not start research until you can state "Company X at domain Y" and the user has confirmed it. Anchor ALL research on that domain; discard any result about a same-named company on a different domain, and never merge facts across domains.
3. **Research, then verify, then write.** WebSearch/WebFetch (plus Tavily if connected) for: what the company does (one plain clause), headcount range, locations, funding stage and total (if public), careers page URL, currently open roles, and 2-3 recent positive news items usable as outreach proof points. Present every finding as a checklist with its source: "Here's what I found. Confirm or correct each line." Explicitly ask whether the careers page and its posted roles are current: careers pages are often stale, and stale postings would seed wrong role defaults in the next step. Only facts the user explicitly confirms or corrects enter the profile. Anything unconfirmed is either dropped or written with a `(unverified)` tag that agents must treat as an Estimate, never a stated fact.
4. **No fact in the profile without a source.** Each organization line records where it came from: `(stated by user)` or `(web, <domain>, confirmed by user)`. Downstream agents (especially Shakespeare, whose outreach states company facts to candidates) rely on this: only `stated` or `confirmed` facts may be asserted in artifacts.

If research finds little (stealth, tiny company), ask for a one-clause descriptor and move on; the profile notes `(stated by user)` on everything.

## 3. What they hire for

Offer chips from the open roles found on their careers page (only if the user confirmed the page is current) plus free text: functions, typical levels, approximate volume. This seeds role defaults; it does not limit what they can run later.

## 4. Constraints (careful, legal)

Explain in one sentence: some searches carry hard eligibility requirements, and the kit only ever uses ones they write themselves. AskUserQuestion with multiSelect: Work authorization / Security clearance / Onsite presence / Professional licensure / Background check / None of these (default None). For each selected: ask for the exact sentence as it should appear to a candidate, show one worked example (e.g. "Must be authorized to work in the United States without current or future visa sponsorship."), and capture gate stage (screen / application / offer) and whether a No ends the process. Expect users to offer quality bars here ("must have shipped products from scratch", "needs 10 years experience"): those are calibration criteria, not eligibility gates. Redirect them to the profile's role defaults, say so in one sentence, and keep the constraints list strictly legal/logistical. Record verbatim. Never draft the legal wording for them beyond showing the example; recommend counsel review in the profile. An empty list means the kit ships no eligibility gate anywhere.

## 5. Tools (optional, say so)

State plainly: everything works with public data alone. Search the connector registry (SearchMcpRegistry) for their ATS and doc tools; suggest via SuggestConnectors if found. Record what is connected in the profile. Do not block on this.

## 5.5 Brain dump (what they already have)

One plain-message invitation, never a chip question: paste or attach anything that should inform every future search. Brand or careers-page copy, an EEO statement, a benefits blurb, comp philosophy or bands, past postings that worked, hiring process notes, or a straight brain dump. Skippable like every step, and skipping costs nothing: the kit runs fully on public data.

File what arrives under `talent-one-kb/` by KB category: `brand/` (voice, EEO, benefits), `benchmarks/` (comp), `internal/` (process notes, calibration), `history/` (past postings). Pasted text becomes a dated `.md` file in the right category, verbatim, never reformatted. Record `kb_root: talent-one-kb/` in the profile's resources so every agent's KB-FIRST step reads it. If they hand over role-specific material (a JD for one particular search), accept it, note which role, and file it to that role's `talent-one-roles/<role_slug>/inputs/` instead.

## 6. Look

Mode chips: Light (editorial, warm paper) / Dark / Dancheong (heritage color). Optional brand color (accept a hex or "our blue is fine"). Ask whether to keep the "Built with Talent One by Onepromptman" footer credit on artifacts (default on). If they pick a custom color, render a quick preview snippet from the pattern library so they see it, not a hex code.

## 7. Write the profile

Write `talent-one-profile.md`: organization (name, descriptor, locations, careers URL, verified proof points with dates), roles (functions, levels, volume), constraints (verbatim, with gate stage and disqualifying flag), branding (mode, primary, accent, credit on/off, artifact prefix from company initials), connectors, resources (`kb_root: talent-one-kb/` when the brain dump filed anything, plus any per-agent context notes), and a `researched:` date stamp. Offer a refresh when the stamp is older than 90 days. Close with the menu: the eight artifacts and the full kit, one line each, "ask for any of these in plain words." Add one line on how quality scales: the kit runs on public data alone, and anything they already hold for a role (an existing JD, an intake doc, comp data, a prior posting) makes the output sharper and skips work; hand it over when starting that role and the kit consumes it instead of regenerating it. Do not collect any of it now: setup is company-level, materials are per-role. Mention once, in one line, how 1.0 runs work: the first run for each role builds a Context Pack (one research pass, 5-10 minutes) and every artifact renders from it in parallel; later runs and updates on that role reuse the pack and are fast. Fastest path, entirely optional: pasting `references/PACK_RESEARCH_PROMPT.md` (in the talent-one skill) into any Claude chat, claude.ai, the app, or a second Cowork tab, and dropping the returned JSON into that role's `inputs/` when they start it, means scout may not need to run at all. Never a prerequisite: the role spec alone is still the minimum input.
