from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyseed_app.engine import AGE_BANDS, MODES, SUBJECTS, generate_prompt  # noqa: E402
from storyseed_app.storage import load_default_state  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic StorySeed sample prompts.")
    parser.add_argument("--count", type=int, default=8)
    parser.add_argument("--matrix", action="store_true", help="Cycle through age bands and subjects for tuning.")
    parser.add_argument("--output-dir", default="")
    args = parser.parse_args()

    state = load_default_state()
    rows = []
    for index in range(args.count):
        seed = 100 + index * 101
        mode = MODES[index % len(MODES)]
        age_band = AGE_BANDS[index % len(AGE_BANDS)] if args.matrix else "8-11"
        subject = SUBJECTS[index % len(SUBJECTS)] if args.matrix else "Creative Writing"
        prompt = generate_prompt(
            state,
            {
                "seed": seed,
                "mode": mode,
                "age_band": age_band,
                "subject": subject,
                "tone": "Playful",
                "creativity": 55 + (index * 7) % 35,
            },
        )
        text = prompt["prompt"]
        rows.append((seed, mode, text))
        print("=" * 78)
        print(f"Seed: {seed} | Mode: {mode} | Age: {age_band} | Subject: {subject}")
        print()
        print(text)
        print()

    if args.output_dir:
        out = Path(args.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        for seed, mode, text in rows:
            slug = mode.lower().replace(" ", "-").replace("?", "").replace("/", "-")
            (out / f"{seed}-{slug}.txt").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
