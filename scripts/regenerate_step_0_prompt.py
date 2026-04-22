#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_FILE = ROOT / "step-0-prompt.txt"
COMMON_TASK_LINE = "Perform the following tasks by using the mounted CSV file."

def read_required_step_file(step: int) -> str:
    p = ROOT / f"step-{step}-prompt.txt"
    if not p.exists():
        raise FileNotFoundError(f"Missing required file: {p.name}")
    return p.read_text(encoding="utf-8")

def extract_tasks_section(step: int, text: str) -> str:
    # Strict: require exact "## Step N Tasks" heading
    heading = f"## Step {step} Tasks"
    start = text.find(heading)
    if start == -1:
        raise ValueError(f"Could not find required heading '{heading}'")

    tasks_block = text[start:].rstrip()

    # Keep only this tasks section (until next level-2 heading, if any)
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

    # Remove repeated "Perform..." line variants.
    filtered: list[str] = []
    for line in body:
        stripped = line.strip()
        normalized = re.sub(r"^\d+\.\s*", "", stripped)
        if normalized == COMMON_TASK_LINE:
            continue
        filtered.append(line)

    # Renumber top-level ordered list items sequentially.
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

def build_merged_prompt(tasks_by_step: dict[int, str]) -> str:
    # ...existing code...
    lines: list[str] = [
        "You are a data processing workflow step.",
        "You are step 0 in the workflow sequence, an all-in-one merged step of steps 1 through 15.",
        "## Important",
        "First, check the mounted TXT file to see if any helper scripts exist yet.",
        "    General file processing helper scripts should be located under the heading \"Generic file processing code with file read loops and filter method hooks\".",
        "    Scripts specific to step 0 should be located under the heading \"Step 0\".",
        "    If no helper scripts exist yet, feel free to write your own Python scripts or Shell script if needed to help you accomplish your tasks.",
        "    If helper scripts do exist, feel free to improve them if needed to help you accomplish your tasks.",
        "For persistence accross workflow runs, you must save any scripts you create or improve.",
        "    Save general file processing helper scripts you create or improve to `output.scripts.file-processing-code`",
        "    Save any task helper scripts you create or improve to `output.scripts.step-0-code`",
        "    The program that ran this workflow will save those scripts when it receives the return output.",
        "You have 29 minutes to complete your tasks, set a timer and be aware of the time.",
        "    This is because OpenAI has set a 30 minute limit on workflow processing tasks.",
        "    If you run out of time:",
        "        Append a message to the `output.errors` array with the message \"Task exeeded 29 minutes.\"",
        "        Be sure to save any scripts you created.",
        "        Stop processing tasks immediately so the output object can be returned to the program that ran this workflow.",
        "        Saving the scripts and returning the output object before time runs out is very important because it will help this workflow step run faster next time.",
        "",
        "## Merged Tasks (from steps 1 through 15)",
        COMMON_TASK_LINE,
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

    merged = build_merged_prompt(tasks_by_step)
    OUT_FILE.write_text(merged, encoding="utf-8")
    print(f"Generated: {OUT_FILE}")

if __name__ == "__main__":
    main()