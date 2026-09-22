# Meeting Transcript → Actionable Plan

An MVP that reads the transcript of a customer discovery call and produces a structured, actionable plan in Markdown.

Built as a take-home task for an AI agency. Internal, but built to customer standard so it can serve as a proof point.

---

## The problem it solves

Time is lost after customer sessions. Not in capturing the conversation - a transcript already exists - and not in asking the right questions, which is the consultant's job. It is lost in the step between: reading a long, fast-moving call and working out what the plan should actually be.

That step is what this tool does.

## The one thing that makes it trustworthy

An agent that reads a transcript and writes a confident plan is easy to build and dangerous to use, because customers do not know what they do not know. If the call never established a deadline, a plan that quietly asserts one is worse than no plan.

So the tool enforces a contract. **Every statement in the output is exactly one of three things:**

| | | |
|---|---|---|
| **Quoted** | a customer-stated fact | carries a verbatim span of transcript underneath it |
| **Inferred** | the agent's judgement | sits under a heading that explicitly says so |
| **Missing** | never established in the call | marked `Not covered in this call`, with follow-up questions drafted |

Two design choices make that contract hold rather than merely stating it:

1. **The Markdown is rendered by Python, not by the model.** The model fills a fixed schema; `render_markdown()` builds the document. Section order and the `Not covered in this call` markers cannot drift between runs.
2. **Quotes are verified with no model involved.** `verify_quotes()` checks each quote is genuinely a substring of the transcript (normalising whitespace and case, so formatting drift isn't mistaken for fabrication). Anything that fails is flagged `[!] quote not verified` in the output and counted in a footer. The grounding claim is therefore checkable, not a promise.

## The three dimensions

The plan is structured around the three things the consultant sets out to establish in a discovery call, so the output maps directly onto the questions asked:

1. **Current Workflow** - how the work is done today, where the customer believes the bottleneck is, how long it takes, how many people are involved
2. **Output** - what they want to be holding at the end, who reads it, and whether it feeds any internal system (which drives format)
3. **Expectations** - when they want it, and what a successful reduction in wasted time would look like

Each dimension can be fully covered, **partially covered** (substance answered, something specific left open), or not covered at all. Follow-up questions from all three are rolled up into one list at the end of the document.

---

## Install

```bash
pip install -r requirements.txt
```

Set your API key (never hardcoded, never committed):

```bash
export ANTHROPIC_API_KEY=your-key-here
```

On Windows PowerShell:

```bash
$env:ANTHROPIC_API_KEY = "your-key-here"
```

## Run

```bash
python plan_agent.py sample_transcript.txt
```

Writes `sample_transcript_plan.md` next to the transcript.

| Flag | Effect |
|---|---|
| `-o PATH` | write somewhere else; `-o -` prints to stdout |
| `--json` | also write `<stem>_plan.json` - the structured output, for feeding a system later |
| `--model` | override the model for one run |

## Configuration

`DEFAULT_MODEL` at the top of `plan_agent.py` is the only place the model is named. It is set to `claude-sonnet-5`: this is structured extraction against a fixed schema rather than open-ended reasoning, so Sonnet is the sensible default on cost and latency. If output quality isn't good enough, change that one line to `claude-opus-5`, or pass `--model claude-opus-5` for a single run with no edit at all.

The system prompt in `plan_agent.py` is the actual product. Tuning the tool means editing that string.

---

## Files

| File | |
|---|---|
| `plan_agent.py` | the whole tool - schema, prompt, verifier, renderer, CLI |
| `sample_transcript.txt` | a fixture: a discovery call with a fictional freight broker |
| `requirements.txt` | `anthropic`, `pydantic` |
| `README.md` | this file |
| `sample_transcript_plan.md` | generated output - the plan produced from the fixture |

The fixture is deliberately uneven. Current Workflow is richly covered; Output is answered in substance but the customer explicitly declines to name a target system; Expectations gets "soon" and "a lot faster" and no hard numbers. One run therefore exercises quoting, partial-gap handling and full-gap handling together.

---

## Limitations

Worth being straight about, since this is an MVP:

- **The fixture is a fixture.** It proves the mechanism works end to end. It cannot tell you whether the recommendations are good on a real call - expect to tune the system prompt against your first genuine transcript.
- **One API call, no chunking.** A very long transcript will hit the token limit; the tool detects this and tells you rather than silently truncating, but it does not yet handle it.
- **Output always needs human review.** The header of every generated plan says so. The tool structures and evidences the thinking; it does not replace the consultant's judgement.
- **No transcript format handling.** Plain text in. Speaker labels and timestamps are passed through untouched, which works fine, but there is no VTT or Teams-export parsing.
- **No tests.** The deterministic half (verifier + renderer) is straightforward to cover and would be the first thing to add.

## Deliberately out of scope

Web UI, live transcription, CRM/TMS integration, multi-transcript memory. All are reasonable additions on top of this shape if the MVP proves useful - the `--json` output exists specifically so the integration path is a small change rather than a rewrite.
