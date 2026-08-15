# Designing Better Skills: Five Principles from a Case Study

*How the `diagram-design` skill (cathrynlavery/diagram-design) illustrates practices that make instruction files work better for both humans and AI agents.*

---

## Why this matters

Most skill files are written once, skimmed by an author who already knows what they meant, and then handed to a model that has never seen them before and has to make split-second decisions from them: *should I even open this file? What do I load? What do I do first?*

The five practices below come from auditing a single, widely-adopted Claude Code skill against how it's actually structured. None of them are exotic. All of them are commonly skipped. Together they form a short, checkable design philosophy: **be loud exactly once (in the description), be quiet everywhere else, load only what's needed, close your own loops, and put anything that must be exact into code instead of prose.**

This document is meant to be used two ways:
- **By a person** drafting or reviewing a skill, as a checklist.
- **By an AI agent** (e.g. Claude using `skill-creator` or writing a skill from scratch) as design guidance to apply directly while authoring.

---

## 1. Treat the description field as purchased trigger surface, not a summary

### The problem

The `description` field in a skill's frontmatter is the *only* thing that's always loaded into the model's context, for every conversation, whether the skill is relevant or not. That scarcity is exactly why most style guides tell you to keep it short — often cited around 100 words.

But short descriptions have a failure mode that's easy to miss: **models under-trigger skills.** Faced with a vague or generic description, a model tends not to reach for the skill at all, even when it would help. This isn't a hypothetical — it's a documented tendency, and it's the reason official skill-authoring guidance recommends descriptions that are deliberately a little "pushy": naming specific contexts and phrasings where the skill should fire, rather than a one-line summary of what it broadly does.

### The practice

`diagram-design` supports 27 distinct diagram types — architecture, flowchart, sequence, state machine, quadrant, Gantt, and so on. Its description runs to roughly 144 words: well past the usual guidance, and it names *every single type*, plus the supported import formats, output formats, and canvas sizes.

That looks, at first glance, like the classic mistake of stuffing the trigger field. It isn't. Here's the reasoning:

> A generic description ("creates diagrams and charts") would make 25 of the skill's 27 capabilities effectively invisible. If a user says "make me a swim lane" or "I need a radar chart" and those words never appeared in the description, the model has no signal to consult the skill for that request — even though the skill can do it perfectly well.

**The reframed rule:** the length budget for a description isn't a word count — it's a function of the number of distinct things the skill can do. A narrow, single-purpose skill earns a short description. A broad skill with many discrete capabilities has to buy visibility for each one, and that costs words. The tax scales with the surface area, and for a broad skill, paying it is a bargain compared to having most of your capabilities silently unreachable.

### How to apply this

| Skill shape | Description strategy |
|---|---|
| One job, one trigger phrase | Keep it to a sentence or two. Padding here is pure cost. |
| Several related capabilities | List the specific contexts/phrasings for each one, not just the umbrella term. |
| Many named sub-capabilities (types, formats, frameworks, languages) | Name them. Every unnamed one is a coin-flip on whether it ever gets used. |

**Practical test:** for each named capability, ask — *if a user asked for this by name, and this exact word never appeared in the description, would the model reliably still find this skill?* If the honest answer is no, the word needs to be in there.

---

## 2. Make progressive disclosure real, not aspirational

### The problem

"Progressive disclosure" is a phrase most skill authors know and few actually implement. The intended structure has three tiers:

1. **Metadata** (name + description) — always in context.
2. **The instruction body** (`SKILL.md` itself) — loaded when the skill triggers.
3. **Bundled resources** (reference docs, scripts, assets) — loaded only on demand, and scripts specifically can *execute* without ever being loaded into context at all.

In practice, most skills collapse tiers 2 and 3 into one giant file. Every trigger pays the full cost of everything the skill could ever need, whether or not the current task touches it.

### The practice

`diagram-design` keeps the tiers genuinely separate, and the resulting ratio is worth internalizing:

- **~32 KB** — the instruction file. This loads on every trigger.
- **~484 KB** — 37 reference documents (one per diagram type, plus onboarding, import procedures, the style guide, and drawing primitives). These load *only* when a specific type or procedure is selected.
- **~1.5 MB** — a finished gallery of example HTML diagrams, three variants each. These are **never** loaded into context. They exist purely so a human can browse a gallery, or so the model can point someone at a rendered example without having read it.

Ask for a flowchart, and the cost is the instruction file plus exactly one type-reference document — roughly a 1-part-loaded : 15-parts-on-demand : 45-parts-never ratio. The other 26 type references cost nothing for that request. Add a 28th diagram type tomorrow, and every *existing* request's context footprint is unchanged.

The instruction file itself is notably larger than a typical skill body — and the case study's own conclusion is worth stating plainly:

> **A big skill isn't a long file. It's a small file with a big library behind it, loaded only in the slice that's relevant.**

### How to apply this

- **Split by variant, not by convenience.** If a skill supports multiple named types, frameworks, or domains (diagram types, cloud providers, file formats, languages), each gets its own reference file. The main instruction body should contain a *selection guide* — enough to route the request — not the content of every variant.
- **Reference files should be self-contained.** A model reading `type-flowchart.md` shouldn't need to also have read `type-sequence.md` to make sense of it.
- **Scripts are a fourth lever, not just storage.** Anything that needs to be deterministic, repetitive, or verified (a linter, a build step, a data extraction routine) belongs in a script that *runs* rather than instructions that get re-interpreted every time. This is the cheapest tier of all — it costs nothing in context unless its output is read back.
- **Assets are not references.** Finished examples, templates, and galleries belong in `assets/`, not `references/` — they're for output and for humans, not for the model to read on every invocation.
- **Test the ratio.** For a representative request, count: what's always loaded, what got loaded for this specific request, and what exists but was never touched. If tier 3 is empty or tiny relative to tier 2, the skill probably isn't actually using progressive disclosure — it's just one file with extra steps.

---

## 3. Let structure carry the enforcement, not capital letters

### The problem

It's tempting to lean on ALWAYS, NEVER, and MUST — in caps — to make sure a model doesn't skip something important. It's also a well-documented yellow flag: heavy use of screamed imperatives is often a sign that the instruction hasn't actually explained *why* something matters, and is instead trying to substitute volume for reasoning. Official skill-writing guidance is explicit about this: if you catch yourself in all-caps NEVER/ALWAYS territory, take it as a signal to stop and reframe with an explanation instead.

### The practice

Across the entire `diagram-design` instruction file — hundreds of lines — there isn't a single screamed imperative. No ALWAYS, no NEVER, no MUST, no DO NOT. Every constraint is instead expressed as one of:

- **A checklist item** the model has to answer, not just obey (*"Would a table or paragraph do the same job? If yes, don't draw."*)
- **A specific, answerable question** (*"Can this node be removed? Would a reader still understand?"*)
- **A numbered gate** the workflow has to pass through before producing output.
- **A table** of budgets, limits, or mappings, rather than a paragraph of prohibitions.

This isn't softer — it's arguably *more* disciplined, because a checklist item has to be specific enough to actually be answerable, whereas "NEVER make ugly diagrams" is unenforceable no matter how many times or how loudly it's repeated.

### How to apply this

When you're about to write a rule, try converting it through this lens:

| Instead of | Try |
|---|---|
| `NEVER use more than one accent color per section.` | `Is the accent color used on more than 1-2 elements? If so, which ones actually deserve focal status?` |
| `ALWAYS check contrast before finalizing.` | A checklist gate: *"Contrast checked against background? If it fails at this size, propose an adjusted value and say why."* |
| `MUST keep responses under 500 words.` | A stated reason (*"long responses get skimmed, not read"*) plus a concrete target, so the constraint is legible rather than arbitrary. |

The underlying test: **could a model fail this rule and have no way to notice?** A shouted imperative can be silently ignored under context pressure. A checklist item that requires an explicit yes/no answer is much harder to skip without the omission being visible.

---

## 4. Design gates that check themselves out of existence

### The problem

Some actions genuinely need a one-time confirmation before proceeding — the kind of thing you don't want to do silently and don't want to ask about *every single time* either. Getting this balance wrong produces either a skill that silently does something the user would object to, or a skill so cautious it interrupts every single invocation with the same question forever.

### The practice

`diagram-design` ships with default visual styling (specific default colors, specific default fonts). Before it draws its first diagram in a new project, it checks whether that default styling has actually been customized. If it hasn't, it stops and asks the user how they'd like to proceed — pull colors from their website, extract from another local design system, paste tokens by hand, or explicitly proceed with the defaults.

The clever part is *how* it detects "already customized," without needing any persistent memory of its own:

> **One-line heuristic: if the shipped default accent color is no longer present, assume the user has already gone through the gate and don't ask again.** No state file, no database, no session tracking — the artifact itself (the style guide) *is* the record. Being different from the default is the signal.

It also states, in a single sentence, exactly what failure mode the gate exists to prevent: shipping obviously default-styled output into a context where it's clearly supposed to be branded. That sentence matters as much as the gate itself — a check with no stated purpose reads as arbitrary friction; a check that names the specific embarrassing outcome it prevents reads as considered judgment.

### How to apply this

Ask three questions about any confirmation gate you're adding:

1. **What's the specific bad outcome this prevents?** Write it down as a sentence in the skill itself. If you can't state it in one sentence, the gate may not be earning its interruption.
2. **How will future invocations know the gate has already been satisfied?** Prefer a check against something that already exists and would visibly differ once the user has acted (a config value, a file's contents, a token that's no longer at its default) over a new piece of state you have to remember to create and maintain.
3. **Does it ask once, or does it nag?** A gate that fires on every single invocation regardless of prior answers trains users to reflexively dismiss it — which defeats the purpose the first time it would have mattered. A gate should be able to detect that it's already been through this once.

---

## 5. Push anything that must be exact into code, and test the code

### The problem

Instructions in prose are good at conveying judgment and intent. They're bad at guaranteeing that something happens *every single time, correctly, without drift* — especially for requirements that are tedious, unglamorous, or easy to silently skip under time pressure. Accessibility is a canonical example: it's the first thing to get dropped when a model (or a person) is moving fast, because skipping it doesn't produce an obviously broken result — it just produces an invisible one.

### The practice

`diagram-design` bundles a linter — over 500 lines — that runs against every generated diagram and checks specific, mechanical accessibility requirements: that the output contains required title and description elements, that they're structured correctly, that labeling attributes correctly reference them, and so on. Critically, the project doesn't stop at the linter — it also ships a separate, substantial test suite *for the linter itself*, so the enforcement mechanism is itself verified rather than trusted on faith.

The result: a model using this skill can be sloppy about accessibility in its reasoning, and it won't matter, because the *output* gets checked by something that doesn't get tired, doesn't skip steps under pressure, and fails loudly rather than silently.

This is the same principle behind the skill's import path, which produces a **fidelity ledger** — a generated report of exactly what was merged, collapsed, or dropped when redrawing an imported diagram. Rather than trusting the model to remember to mention what changed, the mechanism forces an accounting of it as a byproduct of the process itself.

### How to apply this

Use this as a rule of thumb: **if a requirement is (a) mechanically checkable and (b) easy to skip without anyone noticing, it belongs in a script, not a sentence.** Good candidates:

- Structural/format requirements (required fields, valid schema, required accessibility attributes)
- Anything with a numeric threshold (line length, complexity budgets, contrast ratios)
- Anything where "did this actually happen" is more reliable to check after the fact than to trust in the moment
- Anything you've noticed silently regressing in past outputs

And when you do write that script: **write a test for the script too.** A checker that's never itself been checked can develop the exact blind spots it was meant to catch. The trustworthiness of an enforcement mechanism is only as good as the confidence you have that it actually works.

---

## Quick-reference checklist

Use this when drafting or reviewing a skill — for yourself, or as direct instructions if you're an agent authoring one:

- [ ] **Description:** Does every named capability appear as a word or phrase in the description? If not, is that capability effectively invisible to triggering?
- [ ] **Progressive disclosure:** Can you point to content that's in tier 3 (bundled resources) and *not* tier 2 (always-loaded body)? If tier 3 is empty, you likely have one file pretending to be three.
- [ ] **Voice:** Search the draft for ALWAYS / NEVER / MUST in all caps. For each hit, can it be rewritten as a checklist question, a table, or a stated reason instead?
- [ ] **Gates:** For every confirmation step, is there a one-sentence statement of the specific bad outcome it prevents? Is there a way for the skill to detect it's already been satisfied, without a new piece of state to maintain?
- [ ] **Precision:** For every requirement that's exact, mechanical, or easy to silently skip — is it enforced by a script rather than a sentence? Is the script itself tested?

---

*This document summarizes design practices identified through independent analysis of the `cathrynlavery/diagram-design` GitHub repository (skill file, reference documentation, and bundled scripts), cross-referenced against Anthropic's own skill-authoring guidance on progressive disclosure and description design.*
