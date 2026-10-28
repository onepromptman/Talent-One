# Teaching benchmark ranges

> **What this is:** the benchmark ranges the funnel-diagnosis method compares against.
> Add it to a Claude Project's knowledge for the paste-in edition; the `talent-one-funnel`
> skill reads the machine-readable copy in `data/teaching-benchmarks.csv`.
>
> **What these numbers are, honestly:** synthesized, round-number ranges for the
> categories that public recruiting-analytics reports publish each year. They are teaching
> values for practice and quick calibration. They are **not** sourced figures, they are not
> any one company's data, and they carry no confidence grade. Label every one you use as a
> teaching range. Replace them with your own trailing numbers, or with a dated figure from
> a published report you can cite, before you make a high-stakes process change.

---

## How to use this file

1. Match the question to a section below. Funnel and conversion questions go to §1,
   technical-screen questions to §1 and §5, time-to-fill to §2, offers to §3, channels and
   outreach to §4.
2. Prefer the technical column for technical roles; aggregate rates overstate conversion
   for specialized roles.
3. If a metric is not here, do not invent it. Say there is no grounded benchmark and name
   the kind of report that would have it:

| Category | What such reports publish |
|---|---|
| Recruiting funnel and passthrough | Stage-by-stage conversion, interviews per hire |
| Time to hire and time to fill | Days by stage, function and seniority |
| Sourcing and outreach | Open and reply rates, channel yield |
| Offer and acceptance | Offer-accept rates, decline reasons |
| Technical hiring and assessments | Technical screen pass rates, assessment formats |
| Labor market and talent supply | Demand, turnover, remote and hybrid split |

---

## §1 Funnel passthrough

"Pass %" is the share of candidates who reached the earlier stage and advanced to the next.

| Transition | General pass % | Technical-role pass % | Basis |
|---|---|---|---|
| Application to recruiter screen | 25-40% | 20-35% | teaching range |
| Recruiter screen to hiring-manager screen | 45-55% | 45-55% | teaching range |
| Hiring-manager screen to first technical round | 45-55% | 45-55% | teaching range |
| First technical round to next round | 30-40% | 30-40% | teaching range |
| Final round to offer | 60-70% | 60-70% | teaching range |
| Offer to accept | 70-90% | 70-90% | teaching range |

**Reading a gap.** A transition well below its range is the first candidate for the
bottleneck, but read its neighbours before you name it. If candidates who clear a
low-pass transition do unusually well afterwards, that stage's bar is finding the right
people and the question is what is being fed into it. A transition well above its range
can mean the screen before an expensive stage is too lenient, so the cost lands
downstream. If nothing is below its range, there may be no single bottleneck.

**Interviews per hire.** Technical roles commonly run several interviews per hire,
screens included. When a team runs many more final-round interviews than it makes offers,
an upstream screen is usually letting the wrong candidates through.

## §2 Time to fill

| Metric | Range | Basis |
|---|---|---|
| Time to fill, all roles (median) | about 40 days | teaching range |
| Time to fill, technical roles | about 45-60 days | teaching range |
| Time to fill, senior and staff technical roles | about 60-75 days | teaching range |
| Recruiter screen to final round | about 1-2 weeks | teaching range |

## §3 Offer and acceptance

| Metric | Range | Basis |
|---|---|---|
| Offer-accept rate, overall | 70-90% | teaching range |
| Offer-accept rate, competitive technical markets | about 70% | teaching range |
| Most common decline reason | compensation or a competing offer | teaching note |
| Next most common decline reason | role scope, growth or mission fit | teaching note |

## §4 Sourcing, channels and outreach

| Metric | Typical | Strong | Basis |
|---|---|---|---|
| Cold outreach open rate | 35-50% | 65%+ | teaching range |
| Cold outreach reply rate | 8-15% | 25%+ | teaching range |
| Positive-reply rate | 5-10% | 18%+ | teaching range |
| Meeting-booked rate | 3-5% | 10%+ | teaching range |
| Referral conversion versus cold outreach | several times higher | | teaching note |
| Re-engaged past candidates as a share of hires | 10-20% | | teaching range |
| Touches before a first reply | 3-5 | | teaching range |

Referrals usually convert best; past candidates in the ATS or CRM are the cheapest new
pipeline. When re-engaged candidates are a large share of recent hires, run a
re-engagement pass before cold outreach for a new role.

## §5 Technical hiring and assessments

| Metric | Range or note | Basis |
|---|---|---|
| First technical screen pass rate | 30-40% | teaching range |
| Take-home versus live exercise | preferences split | teaching note |
| Candidate drop-off in long processes | rises sharply past about four weeks | teaching note |
| A short technical pre-screen | tends to lift the pass rate of the panel after it | teaching note |
