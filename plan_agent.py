"""
plan_agent.py - turn a customer meeting transcript into an actionable plan.

MVP built as a take-home task for an AI agency. One API call, one Pydantic schema,
one deterministic Markdown renderer.

The contract this tool enforces: every statement in the output is either
  1. quoted   - a customer-stated fact, with verbatim transcript evidence
  2. inferred - the agent's judgement, explicitly labelled as such
  3. missing  - marked "Not covered in this call", with follow-up questions

It never fills a gap with a plausible guess.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import anthropic
from pydantic import BaseModel, Field

# The only place the model is named. This is structured extraction against a
# fixed schema rather than open-ended reasoning, so Sonnet is the sensible
# default on cost and latency. Swap to "claude-opus-5" here (or pass --model)
# if output quality isn't good enough.
DEFAULT_MODEL = "claude-sonnet-5"

MAX_TOKENS = 16000


# --------------------------------------------------------------------------
# Schema - this is what the API is constrained to return
# --------------------------------------------------------------------------

class Finding(BaseModel):
    statement: str = Field(description="One thing the customer established, in plain language.")
    quote: str = Field(description="The verbatim span of transcript that evidences it.")


class Dimension(BaseModel):
    covered: bool = Field(description="True only if the call genuinely established this.")
    findings: list[Finding] = Field(description="Empty when covered is false.")
    gap_note: str = Field(description="What specifically is missing. Empty string if nothing is.")
    follow_up_questions: list[str] = Field(description="Questions that would close the gap.")


class Step(BaseModel):
    title: str
    detail: str


class MeetingPlan(BaseModel):
    customer: str
    problem_statement: str
    current_workflow: Dimension
    desired_output: Dimension
    expectations: Dimension
    recommendation: str
    implementation_steps: list[Step]


# --------------------------------------------------------------------------
# Prompt - the actual product
# --------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a consultant's assistant. You read the transcript of a \
customer discovery call and turn it into an actionable plan.

You extract against three dimensions, because these are the three things the \
consultant sets out to establish in the call:

1. CURRENT WORKFLOW - how the work is done today. How information is collected \
and reviewed, where the customer believes the bottleneck is, how long the process \
takes, and how many people are involved.

2. OUTPUT - what the customer wants to be holding at the end. The form it should \
take, who reads it, and whether it has to feed into any internal system (which \
affects format).

3. EXPECTATIONS - when they want it, and what a successful reduction in wasted \
time would actually look like to them.

THE RULES THAT MATTER MOST

Customers do not know what they do not know. Your value is in being honest about \
what the call did and did not establish, so never paper over a gap.

- Every Finding must carry a `quote` copied character-for-character out of the \
transcript. Copy it exactly: do not paraphrase, tidy, correct or shorten it \
mid-span. Keep it to the span that actually evidences the statement. Never \
invent a quote, and never quote the consultant where you mean the customer.

- If the call did not establish a dimension, set `covered` to false, leave \
`findings` empty, say what is missing in `gap_note`, and write the follow-up \
questions that would close it. Do NOT invent a deadline, a headcount, a duration, \
a target system, a budget or a success metric that nobody said. "Soon" is not a \
date. "A lot faster" is not a metric. A number the customer explicitly called a \
guess is a guess - record it as one in the statement.

- A dimension can be covered and still have a gap. If the customer answered the \
substance but left something specific open, set `covered` to true, record the \
findings, and still use `gap_note` and `follow_up_questions` for the open part.

- `recommendation` and `implementation_steps` are your judgement built on top of \
the findings. Here you may reason beyond what was literally said - propose the \
change and how to implement it - but never restate your own inference as \
something the customer told you. Where a step depends on an unanswered question, \
say so in the step.

- Follow-up questions are a starting point for the consultant to review and \
adapt. Write them as things the consultant might ask, not as a message to be \
sent to the customer unedited.

- `problem_statement` is one or two sentences on the problem the customer is \
actually trying to solve, not a summary of the call.
"""


# --------------------------------------------------------------------------
# Steps
# --------------------------------------------------------------------------

def read_transcript(path: Path) -> str:
    """Plain text in. Speaker labels and timestamps are left intact."""
    if not path.exists():
        sys.exit(f"error: no such file: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        sys.exit(f"error: {path} is empty")
    return text


def extract_plan(client: anthropic.Anthropic, transcript: str, model: str) -> MeetingPlan:
    """One call. The schema does the constraining."""
    response = client.messages.parse(
        model=model,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                "Here is the transcript of a customer discovery call. "
                "Produce the plan.\n\n<transcript>\n" + transcript + "\n</transcript>"
            ),
        }],
        output_format=MeetingPlan,
    )

    if response.stop_reason == "refusal":
        sys.exit("error: the model declined to process this transcript.")
    if response.stop_reason == "max_tokens":
        sys.exit(
            "error: response hit the token limit and is incomplete. "
            f"Raise MAX_TOKENS (currently {MAX_TOKENS}) in plan_agent.py."
        )

    return response.parsed_output


def _normalise(s: str) -> str:
    """Collapse whitespace and case so formatting drift isn't read as fabrication."""
    return re.sub(r"\s+", " ", s).strip().casefold()


def verify_quotes(plan: MeetingPlan, transcript: str) -> dict[int, bool]:
    """
    Deterministic check, no model involved: is each quote genuinely present in
    the transcript? This is what makes the grounding claim checkable rather
    than a promise. Returns {id(finding): verified}.
    """
    haystack = _normalise(transcript)
    verified: dict[int, bool] = {}
    for dim in (plan.current_workflow, plan.desired_output, plan.expectations):
        for finding in dim.findings:
            needle = _normalise(finding.quote).strip('"“”')
            verified[id(finding)] = bool(needle) and needle in haystack
    return verified


# --------------------------------------------------------------------------
# Rendering - section order and gap markers come from Python, not the model,
# so the structure cannot drift between runs.
# --------------------------------------------------------------------------

DIMENSIONS = [
    ("Current Workflow", "current_workflow"),
    ("Output", "desired_output"),
    ("Expectations", "expectations"),
]


def _render_dimension(title: str, n: int, dim: Dimension, verified: dict[int, bool]) -> list[str]:
    out = [f"## {n}. {title}", ""]

    if not dim.covered:
        out.append(f"> **Not covered in this call.** {dim.gap_note}".rstrip())
        out.append("")
        return out

    for finding in dim.findings:
        out.append(f"- {finding.statement}")
        flag = "" if verified.get(id(finding), False) else "  `[!] quote not verified`"
        out.append(f"  > {finding.quote}{flag}")
        out.append("")

    if dim.gap_note:
        out.append(f"> **Partially covered.** {dim.gap_note}")
        out.append("")

    return out


def render_markdown(plan: MeetingPlan, verified: dict[int, bool],
                    transcript_name: str, model: str) -> str:
    lines: list[str] = [
        f"# Actionable Plan - {plan.customer}",
        "",
        f"_Generated from `{transcript_name}` by `{model}`. Not yet reviewed by a human._",
        "",
        "## Problem statement",
        "",
        plan.problem_statement,
        "",
    ]

    for i, (title, attr) in enumerate(DIMENSIONS, start=1):
        lines += _render_dimension(title, i, getattr(plan, attr), verified)

    lines += [
        "## Recommendation",
        "",
        "_Agent judgement, built on the findings above - not customer-stated fact._",
        "",
        plan.recommendation,
        "",
        "## Implementation steps",
        "",
    ]
    for i, step in enumerate(plan.implementation_steps, start=1):
        lines.append(f"{i}. **{step.title}** - {step.detail}")
    lines.append("")

    lines += ["## Questions to take back to the customer", ""]
    any_questions = False
    for title, attr in DIMENSIONS:
        dim: Dimension = getattr(plan, attr)
        if not dim.follow_up_questions:
            continue
        any_questions = True
        lines += [f"**{title}**", ""]
        lines += [f"- {q}" for q in dim.follow_up_questions]
        lines.append("")
    if not any_questions:
        lines += ["_None - the call established all three dimensions._", ""]

    unverified = sum(1 for ok in verified.values() if not ok)
    if unverified:
        lines += [
            "---",
            "",
            f"_{unverified} of {len(verified)} quotes could not be matched to the "
            "transcript and are marked `[!] quote not verified`. Check those before "
            "relying on them._",
            "",
        ]

    return "\n".join(lines)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Turn a customer meeting transcript into an actionable plan.",
    )
    parser.add_argument("transcript", type=Path, help="path to the transcript (plain text)")
    parser.add_argument("-o", "--out", default=None,
                        help="output path (default: <stem>_plan.md; '-' for stdout)")
    parser.add_argument("--json", dest="also_json", action="store_true",
                        help="also write <stem>_plan.json")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"model to use (default: {DEFAULT_MODEL})")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("error: ANTHROPIC_API_KEY is not set. Export it and try again.")

    transcript = read_transcript(args.transcript)
    client = anthropic.Anthropic()

    print(f"Reading {args.transcript.name} ({len(transcript):,} chars) with {args.model}...",
          file=sys.stderr)

    try:
        plan = extract_plan(client, transcript, args.model)
    except anthropic.AuthenticationError:
        sys.exit("error: ANTHROPIC_API_KEY was rejected. Check the key.")
    except anthropic.NotFoundError:
        sys.exit(f"error: unknown model '{args.model}'.")
    except anthropic.RateLimitError as e:
        retry = e.response.headers.get("retry-after", "60")
        sys.exit(f"error: rate limited. Retry after {retry}s.")
    except anthropic.APIConnectionError:
        sys.exit("error: could not reach the API. Check the network connection.")
    except anthropic.APIStatusError as e:
        sys.exit(f"error: API returned {e.status_code}: {e.message}")

    verified = verify_quotes(plan, transcript)
    markdown = render_markdown(plan, verified, args.transcript.name, args.model)

    if args.out == "-":
        print(markdown)
    else:
        out_path = (Path(args.out) if args.out
                    else args.transcript.with_name(f"{args.transcript.stem}_plan.md"))
        out_path.write_text(markdown, encoding="utf-8")
        print(f"Wrote {out_path}", file=sys.stderr)

    if args.also_json:
        json_path = args.transcript.with_name(f"{args.transcript.stem}_plan.json")
        json_path.write_text(json.dumps(plan.model_dump(), indent=2), encoding="utf-8")
        print(f"Wrote {json_path}", file=sys.stderr)

    bad = sum(1 for ok in verified.values() if not ok)
    print(f"{len(verified)} quotes checked, {bad} unverified.", file=sys.stderr)


if __name__ == "__main__":
    main()
