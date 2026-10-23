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

# Talent One: setup wizard

Produce `talent-one-profile.md` in the working folder through a guided conversation. The user should never see YAML, file paths, or jargon. Every question has a safe default and can be skipped. If a partial profile exists (a `setup_incomplete` marker in the file), resume from the first missing section instead of restarting.

## 1. Welcome

One short message: what Talent One makes (the eight artifacts, one line each, listed in execution order: HM calibration brief, educational brief, talent map, JD, interview plan, screen guide, sourcing playbook, outreach campaign; run order is handled automatically), that setup takes about 5 minutes, and the two paths: full setup now, or skip and build one artifact immediately (route to the requested talent-one-* skill; setup can happen later).

## 2. Company (HARD GATE: always ask, never assume)

**Non-negotiable rules for this step:**

1. **ALWAYS ask which company this profile is for, with AskUserQuestion, even when you think you know.** Chat history, Claude memory, project context, the user's email domain, and prior sessions are NOT valid sources for the company identity. Users often work across several companies (their employer, clients, a side business); guessing picks the wrong one and every artifact inherits the error. If context suggests candidates, offer them as options in the question ("Acme Inc / another company"), but the user must pick. Never skip the question.
2. **Confirm identity before researching.** Ask for the company name AND website URL in the same question (the URL is not optional: common-word company names collide with unrelated companies in search). If the name is ambiguous, show the candidates you find and have them pick. Do not start research until you can state "Company X at domain Y" and the user has confirmed it. Anchor ALL research on that domain; discard any result about a same-named company on a different domain, and never merge facts across domains.
3. **Research, then verify, then write.** WebSearch/WebFetch (plus the bundled Exa server when the user has signed in to it) for: what the company does (one plain clause), headcount range, locations, funding stage and total (if public), careers page URL, currently open roles, and 2-3 recent positive news items usable as outreach proof points. Present every finding as a checklist with its source: "Here's what I found. Confirm or correct each line." Explicitly ask whether the careers page and its posted roles are current: careers pages are often stale, and stale postings would seed wrong role defaults in the next step. Only facts the user explicitly confirms or corrects enter the profile. Anything unconfirmed is either dropped or written with a `(unverified)` tag that agents must treat as an Estimate, never a stated fact.
4. **No fact in the profile without a source.** Each organization line records where it came from: `(stated by user)` or `(web, <domain>, confirmed by user)`. Downstream agents (especially Shakespeare, whose outreach states company facts to candidates) rely on this: only `stated` or `confirmed` facts may be asserted in artifacts.

If research finds little (stealth, tiny company), ask for a one-clause descriptor and move on; the profile notes `(stated by user)` on everything.

## 3. What they hire for

Offer chips from the open roles found on their careers page (only if the user confirmed the page is current) plus free text: functions, typical levels, approximate volume. This seeds role defaults; it does not limit what they can run later.

## 4. Constraints (careful, legal)

Explain in one sentence: some searches carry hard eligibility requirements, and the kit only ever uses ones they write themselves. AskUserQuestion with multiSelect: Work authorization / Security clearance / Onsite presence / Professional licensure / Background check / None of these (default None). Then take the selected constraints in two small beats, never both asks at once.

**Beat 1, the wording.** For each selected constraint, ask only for the exact sentence as it should appear to a candidate, and show one worked example (e.g. "Must be authorized to work in the United States without current or future visa sponsorship."). Do not mention stage or disqualifying yet.

**Beat 2, the gate.** Once every sentence is captured, ask for all of them together in one question: at which stage each is checked (screen / application / offer) and whether a No ends the process. Offer sensible defaults and a one-tap "same for all".

Expect users to offer quality bars here ("must have shipped products from scratch", "needs 10 years experience"): those are calibration criteria, not eligibility gates. Redirect them to the profile's role defaults, say so in one sentence, and keep the constraints list strictly legal/logistical. Record verbatim. Never draft the legal wording for them beyond showing the example; never invent an EEO statement or a postal address; recommend counsel review in the profile. An empty list means the kit ships no eligibility gate anywhere.

## 5. Tools (optional, say so)

State plainly: everything works with public data alone. Talent One bundles four connectors; none is required, and in Cowork each has to be added once from the plugin's Connectors tab before it can be signed in to. Check which are live with ToolSearch (`+exa`, `+brightdata`, `+greenhouse`, `+ashby`) and show the user one line each:

- **Exa** (web research): sign in once via OAuth from `/mcp` in Claude Code or the plugin's Connectors tab in Cowork; a free Exa account works. Until then agents use the built-in web search.
- **Bright Data** (search results and page reads behind bot protection, four tools only): sign in once via OAuth from `/mcp` or the Connectors tab. Not signed in means skipped.
- **Greenhouse** or **Ashby** (ATS): sign in once via OAuth from `/mcp` or the Connectors tab. A Greenhouse Site Admin connects first and enables scopes under Dev Center, MCP Access (Dev Center changes need developer permissions): tell them to keep write scopes off and to deselect Candidates and Attachments on the consent screen, because Greenhouse's default read scopes include candidates and applications and the plugin does not block Greenhouse tools one by one. An Ashby Org Admin turns on the MCP Server opt-in; connecting users need Elevated Access. Suggest switching the one they do not use off in `/mcp`.

For any other ATS or document store, search the connector registry (SearchMcpRegistry) and suggest via SuggestConnectors if found. Record what is connected in the profile's `connectors` block, one name per line (`exa`, `brightdata`, `greenhouse`, `ashby`, or the connector's own name), or `none`. The kit's agents reach only these four servers; anything else they connected (a document store, another ATS) is read by you at intake and filed into `inputs/` or the KB. The kit reads candidate pipelines as counts only and never writes to an ATS; say so in one sentence. Do not block on any of this.

## 5.5 Brain dump (what they already have)

One plain-message invitation, never a chip question: paste or attach anything that should inform every future search. Brand or careers-page copy, an EEO statement, a benefits blurb, comp philosophy or bands, past postings that worked, hiring process notes, or a straight brain dump. Skippable like every step; skipping costs nothing beyond the two job-description lines asked for next, because the kit runs fully on public data.

If they skip, ask once more for exactly two things and nothing else, because the job description cannot ship without them and no public source can supply them: the company's equal-opportunity statement and its benefits summary, each as the sentence or short paragraph they want candidates to read (paste from an existing posting is fine; `(none yet)` is an acceptable answer: it files nothing and means JD-Bot will ask again at run time). File whatever they give under `talent-one-kb/brand/`.

**Lint at capture (brand, benefits, EEO text).** Before filing any brand, benefits, or EEO text, check it against the kit's forbidden-phrase list (the "Forbidden phrases" bullet in section 4 of the talent-one skill's `references/00_SHARED_CORE.md`; read it there, do not copy it here) and for em dashes. On a hit, say it plainly right then: the phrase, why the kit refuses it (it is on the kit's forbidden-phrase list; the renderer rejects the hard ones and the QA gate flags the rest), and a one-line rewrite (for "competitive salary", offer to state the range instead). Let them take the edit, keep their wording, or skip; if they keep it, file it verbatim and note the known conflict in the profile so the run does not stall on it later. Never rewrite their EEO statement beyond a phrase they approve.

File what arrives under `talent-one-kb/` by KB category: `brand/` (voice, EEO, benefits), `benchmarks/` (comp), `internal/` (process notes, calibration), `history/` (past postings). Pasted text becomes a dated `.md` file in the right category, verbatim, never reformatted. Record `kb_root: talent-one-kb/` in the profile's resources so every agent's KB-FIRST step reads it. If they hand over role-specific material (a JD for one particular search), accept it, note which role, and file it to that role's `talent-one-roles/<role_slug>/inputs/` instead.

## 6. Look

Mode chips: Light (editorial, warm paper) / Dark / Dancheong. Say in one plain line what Dancheong is: a heritage Korean palette on a green temple-eave ground with an orange primary. Optional brand color (accept a hex or "our blue is fine"). Then one short question: keep the "Built with Talent One by Onepromptman" credit on every document? (default yes). If they pick a custom color, render a quick preview snippet from the pattern library so they see it, not a hex code.

## 7. Write the profile

Write `talent-one-profile.md`: organization (name, descriptor, locations, careers URL, verified proof points with dates), roles (functions, levels, volume), constraints (verbatim, with gate stage and disqualifying flag), branding (`mode`, `primary`, `accent`, `credit` on/off, `prefix` from company initials, default TK), connectors, resources (`kb_root: talent-one-kb/` when the brain dump or the EEO and benefits ask filed anything, plus any per-agent context notes), and a `researched:` date stamp. Offer a refresh when the stamp is older than 90 days. Close with the menu: the eight artifacts and the full kit, one line each, "ask for any of these in plain words." Add one line on how quality scales: the kit runs on public data alone, and anything they already hold for a role (an existing JD, an intake doc, comp data, a prior posting) makes the output sharper and skips work; hand it over when starting that role and the kit consumes it instead of regenerating it. Do not collect any of it now: setup is company-level, materials are per-role. Mention once, in one line, how runs work: the first run for each role builds a Context Pack (one research pass, 5-10 minutes) and every artifact renders from it in parallel; later runs and updates on that role reuse the pack and are fast.

Branding is applied by the renderer, not the agents: the orchestrator passes `branding.credit` as `--credit on|off` and `branding.prefix` as `--prefix` on every render, which stamps the kit mark, the artifact id `<prefix>-NN`, and the footer credit "Built with Talent One by Onepromptman" on every document. Agents no longer write those.

One optional sentence, only if the user is technical: "If you already use deep research in another Claude chat, `references/PACK_RESEARCH_PROMPT.md` in the talent-one skill builds a pack there that you can drop into a role's `inputs/`." Never a default suggestion, never a prerequisite: the role spec alone is the minimum input.
