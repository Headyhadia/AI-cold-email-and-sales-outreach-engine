def parse_hook(text: str) -> str:
    for line in text.strip().splitlines():
        if line.upper().startswith("HOOK:"):
            return line[5:].strip()
    return text.strip()


def parse_subjects(text: str) -> dict:
    subjects = {"curiosity": "", "direct": "", "question": ""}

    for line in text.strip().splitlines():
        upper = line.upper()
        if upper.startswith("CURIOSITY:"):
            subjects["curiosity"] = line[len("CURIOSITY:"):].strip()
        elif upper.startswith("DIRECT:"):
            subjects["direct"] = line[len("DIRECT:"):].strip()
        elif upper.startswith("QUESTION:"):
            subjects["question"] = line[len("QUESTION:"):].strip()

    for key in subjects:
        if not subjects[key]:
            subjects[key] = "[subject not generated — regenerate]"

    return subjects


def parse_followups(text: str) -> dict:
    text_upper = text.upper()

    f1_marker = "FOLLOWUP_1:"
    f2_marker = "FOLLOWUP_2:"

    f1_start = text_upper.find(f1_marker)
    f2_start = text_upper.find(f2_marker)

    followup_1 = ""
    followup_2 = ""

    if f1_start != -1 and f2_start != -1:
        followup_1 = text[f1_start + len(f1_marker):f2_start].strip()
        followup_2 = text[f2_start + len(f2_marker):].strip()
    elif f1_start != -1:
        followup_1 = text[f1_start + len(f1_marker):].strip()
    elif f2_start != -1:
        followup_2 = text[f2_start + len(f2_marker):].strip()

    return {
        "followup_1": followup_1 or text.strip(),
        "followup_2": followup_2 or "",
    }