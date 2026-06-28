from __future__ import annotations

from dataclasses import dataclass
import hashlib
import html
import random
import time
from typing import Any


MODES = [
    "Story Starter",
    "Drawing Prompt",
    "What If?",
    "Vocabulary Quest",
    "Finish The Scene",
    "Class Discussion",
    "Silly Invention",
    "Mystery Hook",
]

AGE_BANDS = ["5-7", "8-11", "12-14", "15+"]
SUBJECTS = ["Creative Writing", "Science", "History", "Feelings", "Adventure", "Silly", "Mystery"]
TONES = ["Calm", "Playful", "Thoughtful", "Adventurous"]
PRIMES = [17, 19, 23, 29, 31, 37, 41]


@dataclass(frozen=True)
class Ingredient:
    label: str
    prime: int
    seed: int
    trace: list[int]


def generate_prompt(state: dict[str, Any], options: dict[str, Any] | None = None) -> dict[str, Any]:
    options = options or {}
    seed = _int_option(options.get("seed"), int(time.time() * 1000) % 1_000_000)
    mode = _choice_option(options.get("mode"), MODES, "Story Starter")
    age_band = _choice_option(options.get("age_band"), AGE_BANDS, "8-11")
    subject = _choice_option(options.get("subject"), SUBJECTS, "Creative Writing")
    tone = _choice_option(options.get("tone"), TONES, "Playful")
    creativity = max(0, min(100, _int_option(options.get("creativity"), 55)))

    rng = random.Random(_stable_seed(seed, mode, age_band, subject, tone, creativity))
    pack = _subject_pack(state, subject)
    character = _pick(rng, state.get("characters"), _fallback_character())
    setting = _pick(rng, state.get("settings"), _fallback_setting())
    object_item = _pick(rng, state.get("objects"), _fallback_object())
    topic = _pick(rng, _preferred_list(pack.get("topics"), state.get("topics")), "friendship")
    constraint = _pick(rng, _combined_list(pack.get("constraints"), state.get("constraints")), "include one question")
    extension = _pick(rng, _combined_list(pack.get("extensions"), state.get("extensions")), "draw the scene")
    discussion = _pick(rng, state.get("discussion_questions"), "What changed?")
    subject_focus = _pick(rng, pack.get("focus"), subject.lower())
    vocabulary = _vocabulary(state, age_band, subject, rng)

    ingredients = [
        _ingredient("character", seed, 0, character.get("name", "someone curious")),
        _ingredient("setting", seed, 1, setting.get("name", "a classroom")),
        _ingredient("object", seed, 2, object_item.get("name", "a strange object")),
        _ingredient("topic", seed, 3, topic),
    ]

    title = _title(mode, character, setting, object_item, rng)
    task, challenge, checklist, teacher_note = _render_mode(
        mode=mode,
        age_band=age_band,
        subject=subject,
        tone=tone,
        creativity=creativity,
        character=character,
        setting=setting,
        object_item=object_item,
        topic=topic,
        vocabulary=vocabulary,
        constraint=constraint,
        extension=extension,
        discussion=discussion,
        subject_focus=subject_focus,
        rng=rng,
    )

    text = _prompt_to_text(
        title,
        mode,
        age_band,
        subject,
        subject_focus,
        task,
        challenge,
        vocabulary,
        checklist,
        extension,
        teacher_note,
        ingredients,
    )
    return {
        "title": title,
        "mode": mode,
        "age_band": age_band,
        "subject": subject,
        "tone": tone,
        "seed": seed,
        "creativity": creativity,
        "subject_focus": subject_focus,
        "task": task,
        "challenge": challenge,
        "vocabulary": vocabulary,
        "checklist": checklist,
        "extension": extension,
        "teacher_note": teacher_note,
        "traffic": {
            "class_setup": "green",
            "prompt_settings": "green",
            "generated_prompt": "green",
            "printable_export": "amber",
        },
        "trace_lines": [_trace_line(item) for item in ingredients],
        "ingredients": [item.__dict__ for item in ingredients],
        "prompt": text,
    }


def prompt_to_text(prompt: dict[str, Any]) -> str:
    if prompt.get("prompt"):
        return str(prompt["prompt"])
    return _prompt_to_text(
        str(prompt.get("title") or "StorySeed Prompt"),
        str(prompt.get("mode") or "Story Starter"),
        str(prompt.get("age_band") or "8-11"),
        str(prompt.get("subject") or "Creative Writing"),
        str(prompt.get("subject_focus") or "classroom writing"),
        str(prompt.get("task") or ""),
        str(prompt.get("challenge") or ""),
        list(prompt.get("vocabulary") or []),
        list(prompt.get("checklist") or []),
        str(prompt.get("extension") or ""),
        str(prompt.get("teacher_note") or ""),
        [],
    )


def prompt_to_html(prompt: dict[str, Any]) -> str:
    title = html.escape(str(prompt.get("title") or "StorySeed Prompt"))
    mode = html.escape(str(prompt.get("mode") or "Story Starter"))
    age = html.escape(str(prompt.get("age_band") or "8-11"))
    subject = html.escape(str(prompt.get("subject") or "Creative Writing"))
    seed = html.escape(str(prompt.get("seed") or ""))
    focus = html.escape(str(prompt.get("subject_focus") or "classroom writing"))
    task = html.escape(str(prompt.get("task") or ""))
    challenge = html.escape(str(prompt.get("challenge") or ""))
    vocabulary = [html.escape(str(word)) for word in prompt.get("vocabulary") or []]
    checklist = [html.escape(str(item)) for item in prompt.get("checklist") or []]
    extension = html.escape(str(prompt.get("extension") or ""))
    teacher_note = html.escape(str(prompt.get("teacher_note") or ""))
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{title}</title>"
        "<style>"
        "body{font-family:Arial,sans-serif;margin:0;background:#eef4f8;color:#102033;line-height:1.5}"
        ".page{max-width:840px;margin:28px auto;background:#fff;padding:34px;border:1px solid #d7e2ea}"
        ".brand{font-size:13px;font-weight:700;color:#2474a6;text-transform:uppercase;letter-spacing:.08em}"
        "h1{font-size:32px;line-height:1.15;margin:8px 0 8px}.meta{color:#52687d;margin:0 0 22px}"
        ".name-row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin:18px 0 24px}"
        ".line{border-bottom:1px solid #9fb0bf;min-height:28px;color:#607489;font-size:13px}"
        ".box{border:1px solid #d7e2ea;border-radius:8px;padding:18px;margin:14px 0;background:#fbfdff}"
        ".student{border-left:7px solid #2474a6}.teacher{border-left:7px solid #2d9366;background:#f5fbf8}"
        "h2{font-size:18px;margin:0 0 10px}ul{margin:8px 0 0 22px;padding:0}.vocab span{display:inline-block;border:1px solid #c9dbe8;border-radius:18px;padding:6px 10px;margin:4px 6px 4px 0}"
        ".write-lines{margin-top:18px}.write-lines div{height:30px;border-bottom:1px solid #c7d4df}"
        "@media print{body{background:#fff}.page{margin:0;max-width:none;border:0;padding:18mm;box-shadow:none}.no-print{display:none}.box{break-inside:avoid}.name-row{grid-template-columns:1fr 1fr 1fr}}"
        "</style></head><body><main class=\"page\">"
        "<div class=\"brand\">StorySeed Classroom Worksheet</div>"
        f"<h1>{title}</h1><p class=\"meta\">{mode} | Age {age} | {subject} | Focus: {focus} | Seed {seed}</p>"
        "<section class=\"name-row\"><div class=\"line\">Name</div><div class=\"line\">Date</div><div class=\"line\">Class</div></section>"
        f"<section class=\"box student\"><h2>Student Task</h2><p>{task}</p></section>"
        f"<section class=\"box\"><h2>Challenge</h2><p>{challenge}</p></section>"
        f"<section class=\"box vocab\"><h2>Vocabulary</h2>{''.join(f'<span>{word}</span>' for word in vocabulary)}</section>"
        f"<section class=\"box\"><h2>Success Checklist</h2>{_html_list(checklist)}</section>"
        f"<section class=\"box\"><h2>Extension</h2><p>{extension}</p></section>"
        "<section class=\"write-lines\"><div></div><div></div><div></div><div></div><div></div><div></div></section>"
        f"<section class=\"box teacher\"><h2>Teacher Notes</h2><p>{teacher_note}</p></section>"
        "<p class=\"meta no-print\">Print from your browser for a clean one-page worksheet.</p>"
        "</main></body></html>"
    )


def _render_mode(
    *,
    mode: str,
    age_band: str,
    subject: str,
    tone: str,
    creativity: int,
    character: dict[str, Any],
    setting: dict[str, Any],
    object_item: dict[str, Any],
    topic: str,
    vocabulary: list[str],
    constraint: str,
    extension: str,
    discussion: str,
    subject_focus: str,
    rng: random.Random,
) -> tuple[str, str, list[str], str]:
    name = character.get("name", "a curious learner")
    trait = character.get("trait", "notices something unusual")
    wish = character.get("wish", "wants to help")
    wish_text = _clean_wish(wish)
    place = setting.get("name", "the classroom")
    texture = setting.get("texture", "something feels different today")
    obj = object_item.get("name", "a strange object")
    twist = object_item.get("twist", "changes the plan")
    vocab = ", ".join(vocabulary)
    focus_line = f"Use the {subject.lower()} focus of {subject_focus}."

    if mode == "Drawing Prompt":
        task = f"Draw {place} after {obj} changes one classroom rule. Show {name} nearby, noticing that {texture}."
        challenge = f"Add three labels: one for the setting, one for the object, and one for the idea of {topic}. {focus_line}"
        checklist = ["Include the character", "Show the object doing something", "Label three details", "Make one label explain the subject focus"]
    elif mode == "What If?":
        task = f"What if {obj} appeared in {place} and {twist}? Write what happens when {name} tries to understand it."
        challenge = f"Use {vocab}. Make the answer connect to {subject_focus}."
        checklist = ["Explain the unusual change", "Show one choice", "Use the vocabulary words", "Make the subject link clear"]
    elif mode == "Vocabulary Quest":
        task = f"Use {vocab} in a short quest where {name} travels through {place} to solve a problem about {topic}."
        challenge = f"Each vocabulary word should matter to the story, not just appear in a sentence. Also {constraint}. Link the quest to {subject_focus}."
        checklist = ["Use every vocabulary word", "Make the meaning clear", "Finish with a discovery", "Show the words through action"]
    elif mode == "Finish The Scene":
        task = f"Finish this scene: {name} found {obj} in {place}. The first clue was simple: {texture}."
        challenge = f"Continue for two paragraphs. Reveal why {name} wants to {wish_text}, and {constraint}. Keep {subject_focus} in the background of the scene."
        checklist = ["Continue the scene", "Reveal a motive", "End with a hook", "Use one detail from the setting"]
    elif mode == "Class Discussion":
        task = f"Discuss this question: {discussion}"
        challenge = f"Use {name}, {place}, and {obj} as examples. Link the discussion to {topic} and {subject_focus}."
        checklist = ["Give one idea", "Build on someone else's idea", "Use evidence from the prompt", "Ask one respectful follow-up question"]
    elif mode == "Silly Invention":
        task = f"Invent a classroom gadget using {obj}. It must help {name}, but it accidentally changes {place}."
        challenge = f"Name the invention, explain three rules, and include the words {vocab}. Keep the joke kind and connect it to {subject_focus}."
        checklist = ["Name the invention", "Explain how it works", "Add one funny problem", "Keep the silliness classroom-safe"]
    elif mode == "Mystery Hook":
        task = f"Write the opening to a mystery where {obj} is missing from {place}, even though {name} saw it one minute ago."
        challenge = f"Give three clues. One clue should be useful, one misleading, and one connected to {topic}. Use {subject_focus} to make the clues fair."
        checklist = ["Introduce the mystery", "Add three clues", "Keep the ending unresolved", "Make one clue possible to spot early"]
    else:
        task = f"{name.title()} arrives at {place} and finds {obj}. The place feels unusual because {texture}."
        challenge = f"Write the first page of the story. Include {vocab}, and {constraint}. Bring in {subject_focus} without turning it into a lecture."
        checklist = ["Introduce the character", "Show the strange problem", "End with a question or surprise", "Use one subject detail naturally"]

    if age_band == "5-7":
        checklist = checklist[:2] + ["Use clear sentences"]
    elif age_band in {"12-14", "15+"}:
        checklist.append("Add a thoughtful reason behind the choice")

    if creativity > 74:
        challenge += " Let one ordinary detail behave in an impossible but gentle way."
    elif creativity < 30:
        challenge += " Keep the idea close to everyday classroom life."

    teacher_note = f"{tone} tone. Suitable for age {age_band}. Subject focus: {subject_focus}. Extension: {extension}."
    return task, challenge, checklist, teacher_note


def _prompt_to_text(
    title: str,
    mode: str,
    age_band: str,
    subject: str,
    subject_focus: str,
    task: str,
    challenge: str,
    vocabulary: list[str],
    checklist: list[str],
    extension: str,
    teacher_note: str,
    ingredients: list[Ingredient],
) -> str:
    lines = [
        title.upper(),
        "",
        f"Mode: {mode} | Age: {age_band} | Subject: {subject}",
        f"Subject Focus: {subject_focus}",
        "",
        "Student Task:",
        task,
        "",
        "Challenge:",
        challenge,
        "",
        "Vocabulary:",
        ", ".join(vocabulary) if vocabulary else "Choose three useful words.",
        "",
        "Success Checklist:",
    ]
    lines.extend([f"- {item}" for item in checklist])
    lines.extend(["", "Extension:", extension, "", "Teacher Note:", teacher_note])
    if ingredients:
        lines.extend(["", "Why This Prompt Happened:"])
        lines.extend([f"- {_trace_line(item)}" for item in ingredients])
    return "\n".join(lines)


def _title(mode: str, character: dict[str, Any], setting: dict[str, Any], object_item: dict[str, Any], rng: random.Random) -> str:
    place = str(setting.get("name", "Classroom")).title()
    obj = str(object_item.get("name", "Object")).title()
    starts = {
        "Drawing Prompt": ["Draw", "Picture Prompt For", "Inside"],
        "What If?": ["What If", "Suppose"],
        "Vocabulary Quest": ["The Word Trail Through", "Quest For"],
        "Finish The Scene": ["Finish The Scene At", "The Next Line In"],
        "Class Discussion": ["Talk About", "The Question Inside"],
        "Silly Invention": ["The Invention Called", "Build"],
        "Mystery Hook": ["The Case Of", "Missing From"],
    }
    prefix = rng.choice(starts.get(mode, ["The Day", "The Secret Of"]))
    if mode in {"What If?", "Silly Invention", "Mystery Hook"}:
        return f"{prefix} {obj}"
    if prefix == "The Day":
        return f"The Day At {place}"
    return f"{prefix} {place}"


def _vocabulary(state: dict[str, Any], age_band: str, subject: str, rng: random.Random) -> list[str]:
    vocab = state.get("vocabulary", {})
    words = vocab.get(age_band) if isinstance(vocab, dict) else []
    pack_vocab = _subject_pack(state, subject).get("vocabulary", {})
    subject_words = pack_vocab.get(age_band) if isinstance(pack_vocab, dict) else []
    pool = [str(word) for word in _combined_list(words, subject_words) if str(word).strip()]
    if len(pool) < 3:
        pool = ["curious", "signal", "mistake", "kind", "pattern"]
    return rng.sample(pool, k=min(4, len(pool)))


def _subject_pack(state: dict[str, Any], subject: str) -> dict[str, Any]:
    packs = state.get("subject_packs")
    if isinstance(packs, dict) and isinstance(packs.get(subject), dict):
        return packs[subject]
    return {}


def _combined_list(*values: object) -> list[Any]:
    combined: list[Any] = []
    seen: set[str] = set()
    for value in values:
        if isinstance(value, list):
            for item in value:
                key = str(item).strip().lower()
                if key and key not in seen:
                    seen.add(key)
                    combined.append(item)
    return combined


def _preferred_list(preferred: object, fallback: object) -> list[Any]:
    preferred_items = _combined_list(preferred)
    return preferred_items if preferred_items else _combined_list(fallback)


def _html_list(items: list[str]) -> str:
    if not items:
        return "<p>No checklist supplied.</p>"
    return "<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"


def _ingredient(label: str, seed: int, index: int, value: str) -> Ingredient:
    prime = PRIMES[(seed + index) % len(PRIMES)]
    start = (_stable_seed(seed, label, value) % (prime - 1)) + 1
    trace = []
    current = start
    for step in range(7):
        current = (current * (index + 3) + step + len(value)) % prime
        trace.append(current)
    return Ingredient(label=label, prime=prime, seed=start, trace=trace)


def _trace_line(item: Ingredient) -> str:
    return f"{item.label}: Z{item.prime}, seed {item.seed}, trace {item.trace}"


def _stable_seed(*parts: object) -> int:
    raw = "|".join(str(part) for part in parts).encode("utf-8")
    return int(hashlib.sha256(raw).hexdigest()[:16], 16)


def _choice_option(value: object, allowed: list[str], fallback: str) -> str:
    text = str(value or "").strip()
    return text if text in allowed else fallback


def _int_option(value: object, fallback: int) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return fallback


def _pick(rng: random.Random, values: object, fallback: Any) -> Any:
    if isinstance(values, list) and values:
        return rng.choice(values)
    return fallback


def _fallback_character() -> dict[str, str]:
    return {"name": "a curious learner", "trait": "asks good questions", "wish": "wants to help"}


def _fallback_setting() -> dict[str, str]:
    return {"name": "the classroom", "texture": "the room feels ready for a story"}


def _fallback_object() -> dict[str, str]:
    return {"name": "a curious pencil", "twist": "writes one extra clue"}


def _clean_wish(value: object) -> str:
    text = str(value or "help").strip()
    lowered = text.lower()
    if lowered.startswith("to "):
        return text[3:]
    if lowered.startswith("wants to "):
        return text[9:]
    return text
