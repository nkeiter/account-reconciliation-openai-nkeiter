#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_FILE = ROOT / "step-0-prompt.txt"
COMMON_TASK_LINE = "Perform the following tasks by using the mounted CSV file."
MERGED_HEADING = "## Merged Tasks (from steps 1 through 15)"

def read_required_step_file(step: int) -> str:
    p = ROOT / f"step-{step}-prompt.txt"
    if not p.exists():
        raise FileNotFoundError(f"Missing required file: {p.name}")
    return p.read_text(encoding="utf-8")

def extract_tasks_section(step: int, text: str) -> str:
    heading = f"## Step {step} Tasks"
    start = text.find(heading)
    if start == -1:
        raise ValueError(f"Could not find required heading '{heading}' in step-{step}-prompt.txt")

    tasks_block = text[start:].rstrip()

    # Keep only this step section up to next level-2 heading.
    m = re.search(r"\n##\s+.+", tasks_block[len(heading):])
    if m:
        cutoff = len(heading) + m.start()
        tasks_block = tasks_block[:cutoff].rstrip()

    return tasks_block

def strip_common_instruction_and_renumber(tasks_block: str) -> str:
    lines = tasks_block.splitlines()
    if not lines:
        return tasks_block

    heading = lines[0]
    body = lines[1:]

    filtered: list[str] = []
    for line in body:
        stripped = line.strip()
        normalized = re.sub(r"^\d+\.\s*", "", stripped)
        if normalized == COMMON_TASK_LINE:
            continue
        filtered.append(line)

    renumbered: list[str] = []
    n = 1
    for line in filtered:
        m = re.match(r"^(\d+)\.\s+(.*)$", line.strip())
        if m:
            renumbered.append(f"{n}. {m.group(2)}")
            n += 1
        else:
            renumbered.append(line)

    return "\n".join([heading, *renumbered]).rstrip()

def split_template_step0(text: str) -> tuple[str, str]:
    """
    Returns:
      preamble_through_heading: everything up to and including MERGED_HEADING line
      common_line: preserved common task instruction line if present; otherwise default
    """
    idx = text.find(MERGED_HEADING)
    if idx == -1:
        raise ValueError(f"'{MERGED_HEADING}' not found in step-0-prompt.txt")

    pre = text[:idx].rstrip("\n")
    after = text[idx + len(MERGED_HEADING):]

    # Preserve the first non-empty line after heading as common task line if it matches expectation.
    common_line = COMMON_TASK_LINE
    for raw in after.splitlines():
        candidate = raw.strip()
        if not candidate:
            continue
        if candidate == COMMON_TASK_LINE:
            common_line = candidate
        break

    preamble_through_heading = f"{pre}\n{MERGED_HEADING}"
    return preamble_through_heading, common_line

def build_from_existing_template(tasks_by_step: dict[int, str]) -> str:
    existing = OUT_FILE.read_text(encoding="utf-8") if OUT_FILE.exists() else ""
    if not existing:
        raise FileNotFoundError(
            "step-0-prompt.txt not found. Create it first (with desired boilerplate format), then rerun."
        )

    preamble_through_heading, common_line = split_template_step0(existing)

    lines: list[str] = [
        preamble_through_heading,
        common_line,
        "",
    ]

    for step in range(1, 16):
        lines.append(f"### Source: step-{step}-prompt.txt")
        lines.append(tasks_by_step[step])
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"

def main() -> None:
    tasks_by_step: dict[int, str] = {}
    for step in range(1, 16):
        text = read_required_step_file(step)
        tasks = extract_tasks_section(step, text)
        tasks_by_step[step] = strip_common_instruction_and_renumber(tasks)

    merged = build_from_existing_template(tasks_by_step)
    OUT_FILE.write_text(merged, encoding="utf-8")
    print(f"Generated: {OUT_FILE}")

if __name__ == "__main__":
    main()