# Funnel diagnosis: the RCAR prompt

The hiring manager asks the question you hear every week, "why aren't we closing this?"
Instead of asking an AI lazily, build the brief field by field. This is the prompt the
Oracle runs against the benchmark ranges.

## The lazy version (don't)

```
Why aren't we closing this req? Here's the funnel.
```

You will get: "Post on more boards. Source harder. Speed up the process. Improve your
brand." True, useless, and writeable without any AI. It never tells you which stage is
broken.

## The RCAR version (do)

```
Role: A recruiting-operations analyst who reads funnels against benchmark
ranges, someone who has seen a hundred of these and knows what normal looks like.

Context: This funnel, stage by stage, plus the benchmark range for each
transition. [Paste the counts, or let the project pull them through a connector.]

Action: Compute every transition from the counts. Find the ONE broken
transition, or say there is no single bottleneck. Compare it with its range.
Recommend a specific, operational fix, not "source harder".

Result: The bottleneck, the benchmark gap, the specific fix, and the exact
conversation to have with the hiring manager.
```

## Worked example (the sample funnel)

The synthetic funnel in `data/sample-funnel.csv`: a Staff Backend Engineer req, 220
applications in, 7 offers out (the file stops at offers, so acceptance is unknown):

```
Applications            220
Recruiter screen        132   (60.0% of applications)
Hiring-manager screen    66   (50.0% of recruiter screens)
V1 technical             13   (19.7% of hiring-manager screens)
V2 final                  9   (69.2% of V1 technical)
Offer                     7   (77.8% of V2 final)
```

<!-- WORKED-EXAMPLE:BEGIN -->
What a good answer lands on:

> **Bottleneck:** hiring-manager screen to V1 technical. Only 13 of 66 candidates the
> hiring manager screened reach the first technical round (19.7%) against a 45-55%
> teaching range. The recruiter screen is on range at 50.0% (66 of 132), and the
> candidates who do clear the hiring manager pass V1 technical at 69.2% (9 of 13)
> against 30-40%: the hiring manager's bar finds the right people but rejects most of what
> it is sent.
>
> **Fix:** not "source harder". Write the hiring manager's bar down: a 30-minute
> calibration on the last ten hiring-manager-screen rejections, turned into a shared
> scorecard the recruiter screen applies.
>
> **HM conversation:** "Of the 66 candidates you screened, 13 moved on to the technical
> round (19.7%); a typical rate is 45-55%. The ones who moved on passed it at 69.2%, so
> your bar works. Can we turn your reasons for the last ten rejections into a scorecard I
> apply before you see anyone?"
<!-- WORKED-EXAMPLE:END -->

**Why it works:** the four RCAR fields force the questions a good analyst answers before
diagnosing: who should think about this, what the data is and what normal looks like,
what the actual job is, and what shape the answer should take. The lazy prompt skips all
four and you get platitudes. Swap the funnel for your own and run it.

> **Tip:** end with the counter-argument. For a funnel that is one req over one quarter,
> the honest caveat is sample size: ask what would confirm the diagnosis before you change
> the whole team's process.
