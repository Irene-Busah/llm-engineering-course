"""Choose posts to hand-label, and label them in a small web app.

The labels are the answer key used to score ``extract.py``. They are never part
of the knowledge base.

Usage:
    python label.py select     # choose 50 posts -> data/to_label.jsonl
    python label.py app        # open the labeling app in the browser

Files:
    data/raw.jsonl        input, written by fetch.py
    data/to_label.jsonl   the chosen posts, each with the reason it was chosen
    data/labeled.jsonl    your answers, one line per post. Safe to stop and
                          resume; saving a post again replaces its label.

Labeling rules:
    Record only what the post states. Leave a field empty, or choose "unclear",
    when the post does not say. Never guess. The summary is not labeled.

Roles are typed one per line, with parts separated by ``|``::

    title | location | salary_min | salary_max | currency | period | skills

Every part after the title is optional. Leave a part empty (or type None, N/A or -)
when the post does not give it. One role per line: a post with three roles gets
three lines. Example::

    Senior Full Stack Engineer | San Francisco, CA | 150000 | 200000 | USD | year | TypeScript, React

Requires ``gradio`` for the ``app`` command only.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from pydantic import ValidationError

from schema import Extraction, LabeledPost, RawPost, Role

DEFAULT_RAW = Path("data/raw.jsonl")
DEFAULT_TO_LABEL = Path("data/to_label.jsonl")
DEFAULT_LABELED = Path("data/labeled.jsonl")

# --------------------------------------------------------------------------- #
# Part 1: choosing which posts to label
# --------------------------------------------------------------------------- #

_ENGLISH_STOPWORDS = {
    "the", "and", "to", "of", "in", "for", "a", "with", "we", "you", "is", "are",
    "our", "on", "that", "this", "will", "your", "be", "as", "an", "it", "at", "by", "or",
}
_REMOTE_WORDS = re.compile(r"\b(?:remote|on-?site|hybrid)\b", re.IGNORECASE)
_VISA = re.compile(r"\bvisa\b", re.IGNORECASE)
_SALARY = re.compile(r"[$€£]\s?\d|\b\d{2,3}\s?k\b", re.IGNORECASE)
_EMAIL = re.compile(r"[\w.+-]+(?:@|\s?\[at\]\s?)[\w-]+(?:\.|\s?\[dot\]\s?)[\w.-]+", re.IGNORECASE)


def _first_line(text: str) -> str:
    return text.split("\n", 1)[0]


def looks_non_english(text: str) -> bool:
    """Guess whether a post is mostly not English.

    English job posts are about 28% common English words ("the", "and", "to").
    Dutch and German posts are far lower. Short posts are never flagged, since
    there is too little text to judge.
    """
    words = re.findall(r"[A-Za-zÀ-ÿ']+", text.lower())
    if len(words) < 40:
        return False
    return sum(w in _ENGLISH_STOPWORDS for w in words) / len(words) < 0.15


# (reason, test, how many of the default 50). Rarest first, so rare cases are not
# used up by common ones. "repost" is handled separately below.
_CATEGORIES: list[tuple[str, Callable[[RawPost], bool], int]] = [
    ("junk", lambda p: len(p.text) < 100, 2),
    ("non_english", lambda p: looks_non_english(p.text), 3),
    ("visa_mentioned", lambda p: bool(_VISA.search(p.text)), 4),
    ("repost", lambda p: False, 6),
    ("multi_role_header", lambda p: len(p.text) >= 100 and _first_line(p.text).count(",") >= 2, 6),
    ("no_pipe_header", lambda p: len(p.text) >= 100 and "|" not in _first_line(p.text), 6),
    ("no_remote_mention", lambda p: len(p.text) >= 100 and not _REMOTE_WORDS.search(p.text), 5),
    ("salary_figure", lambda p: bool(_SALARY.search(p.text)), 4),
    ("email_apply", lambda p: bool(_EMAIL.search(p.text)), 3),
]


def _key(post: RawPost) -> tuple[str, int]:
    return (post.source, post.post_id)


def select_posts(posts: list[RawPost], n: int = 50, seed: int = 7) -> list[tuple[RawPost, str]]:
    """Choose ``n`` posts that cover the hard cases, not just the easy ones.

    A random sample would be mostly ordinary posts and would not show where the
    schema breaks. This picks a few of each hard case (see ``_CATEGORIES``), then
    fills the rest at random. The same ``seed`` always gives the same posts.

    Args:
        posts: All collected posts.
        n: How many posts to choose.
        seed: Random seed.

    Returns:
        ``(post, reason)`` pairs in shuffled order, so the hard cases are mixed
        with ordinary posts. If there are fewer than ``n`` posts, all of them.
    """
    rng = random.Random(seed)
    if len(posts) <= n:
        pairs = [(p, "all_posts") for p in posts]
        rng.shuffle(pairs)
        return pairs

    chosen: dict[tuple[str, int], str] = {}
    by_key = {_key(p): p for p in posts}
    scale = n / 50

    def take(candidates: list[RawPost], quota: int, reason: str) -> None:
        pool = [p for p in candidates if _key(p) not in chosen]
        for post in rng.sample(pool, min(quota, len(pool))):
            chosen[_key(post)] = reason

    def take_reposts(quota: int) -> None:
        """Pick pairs of posts by one author in two different months."""
        threads: dict[str, dict[int, list[RawPost]]] = defaultdict(lambda: defaultdict(list))
        for p in posts:
            if p.author:
                threads[p.author][p.thread_id].append(p)
        authors = sorted(a for a, t in threads.items() if len(t) >= 2)
        rng.shuffle(authors)
        picked = 0
        for author in authors:
            if picked >= quota:
                break
            for thread_id in rng.sample(sorted(threads[author]), 2):
                post = rng.choice(threads[author][thread_id])
                if _key(post) not in chosen:
                    chosen[_key(post)] = "repost"
                    picked += 1

    for reason, test, base_quota in _CATEGORIES:
        quota = max(1, round(base_quota * scale))
        if reason == "repost":
            take_reposts(quota)
        else:
            take([p for p in posts if test(p)], quota, reason)

    take([p for p in posts if len(p.text) >= 100], n - len(chosen), "random")
    items = list(chosen.items())[:n]
    pairs = [(by_key[k], reason) for k, reason in items]
    rng.shuffle(pairs)
    return pairs


def load_raw_posts(path: Path) -> list[RawPost]:
    """Load ``RawPost`` records from a JSONL file."""
    with open(path, encoding="utf-8") as f:
        return [RawPost.model_validate_json(line) for line in f if line.strip()]


def _write_lines(path: Path, lines: list[str]) -> None:
    """Write lines to ``path`` so that a crash never leaves a half-written file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("".join(line + "\n" for line in lines), encoding="utf-8")
    os.replace(tmp, path)


def write_selection(pairs: list[tuple[RawPost, str]], path: Path) -> None:
    """Save chosen posts as JSON lines: ``{"reason": ..., "post": {...}}``."""
    _write_lines(path, [
        json.dumps({"reason": reason, "post": json.loads(post.model_dump_json())}, ensure_ascii=False)
        for post, reason in pairs
    ])


def load_queue(path: Path) -> list[tuple[RawPost, str]]:
    """Load the chosen posts written by :func:`write_selection`."""
    queue = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                queue.append((RawPost.model_validate(row["post"]), row["reason"]))
    return queue


# --------------------------------------------------------------------------- #
# Part 2: turning what you type into a validated label
# --------------------------------------------------------------------------- #

ROLE_PARTS = 7   # title | location | min | max | currency | period | skills


def _explain(error: ValidationError) -> str:
    """Turn a validation error into one readable sentence."""
    return "; ".join(f"{'.'.join(map(str, e['loc'])) or 'value'}: {e['msg']}" for e in error.errors())


def _optional(text: str | None) -> str | None:
    text = (text or "").strip()
    return text or None


def _split(text: str | None, separators: str) -> list[str]:
    return [part.strip() for part in re.split(separators, text or "") if part.strip()]


_EMPTY_WORDS = {"none", "null", "n/a", "na", "-", "–", "—"}


def _blank(text: str) -> str:
    """Treat ``None``, ``N/A`` and ``-`` typed in a role part as empty."""
    return "" if text.strip().lower() in _EMPTY_WORDS else text


def _whole_number(text: str, what: str) -> int | None:
    text = text.strip().replace(",", "").replace("_", "")
    if not text:
        return None
    if not text.isdigit():
        raise ValueError(f"{what} must be a whole number such as 100000, not '{text}'")
    return int(text)


def parse_roles(text: str | None) -> list[Role]:
    """Parse the roles box: one role per line, parts separated by ``|``.

    Raises:
        ValueError: With the line number, if a line cannot be understood.
    """
    roles = []
    for number, line in enumerate((text or "").splitlines(), start=1):
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) > ROLE_PARTS:
            raise ValueError(f"Role line {number}: at most {ROLE_PARTS} parts separated by '|', got {len(parts)}")
        title, *rest = parts + [""] * (ROLE_PARTS - len(parts))
        location, low, high, currency, period, skills = (_blank(part) for part in rest)
        try:
            roles.append(Role(
                title=title,
                location=_optional(location),
                salary_min=_whole_number(low, "salary_min"),
                salary_max=_whole_number(high, "salary_max"),
                currency=(_optional(currency) or "").upper() or None,
                salary_period=_optional(period),
                skills=_split(skills, r"[,;]"),
            ))
        except ValidationError as error:
            raise ValueError(f"Role line {number}: {_explain(error)}") from None
        except ValueError as error:
            raise ValueError(f"Role line {number}: {error}") from None
    return roles


def format_roles(roles: list[Role]) -> str:
    """The reverse of :func:`parse_roles`, used to show an existing label."""
    def cell(value: object) -> str:
        return "" if value is None else str(value)
    return "\n".join(
        " | ".join([r.title, cell(r.location), cell(r.salary_min), cell(r.salary_max),
                    cell(r.currency), cell(r.salary_period), ", ".join(r.skills)]).rstrip(" |")
        for r in roles
    )


FIELDS = [
    "is_opportunity", "company", "remote_policy", "remote_scope", "locations",
    "employment_types", "visa_sponsorship", "language_required", "apply_method",
    "apply_target", "deadline", "roles", "note",
]
DEFAULT_FORM = {
    "is_opportunity": True, "company": "", "remote_policy": "unclear", "remote_scope": "",
    "locations": "", "employment_types": [], "visa_sponsorship": "unclear",
    "language_required": "", "apply_method": "unclear", "apply_target": "",
    "deadline": "", "roles": "", "note": "",
}


def build_label(post: RawPost, form: dict, labeled_at: str | None = None) -> LabeledPost:
    """Build a validated label from the values typed in the form.

    Raises:
        ValueError: With a readable message if any value is not valid.
    """
    labeled_at = labeled_at or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    try:
        if not form["is_opportunity"]:
            extraction = Extraction(is_opportunity=False)       # nothing else applies
        else:
            extraction = Extraction(
                is_opportunity=True,
                company=_optional(form["company"]),
                remote_policy=form["remote_policy"],
                remote_scope=_optional(form["remote_scope"]),
                locations=_split(form["locations"], r"\n"),
                employment_types=form["employment_types"] or [],
                visa_sponsorship=form["visa_sponsorship"],
                language_required=_split(form["language_required"], r"[,\n]"),
                apply_method=form["apply_method"],
                apply_target=_optional(form["apply_target"]),
                deadline=_optional(form["deadline"]),
                roles=parse_roles(form["roles"]),
            )
        return LabeledPost(post_id=post.post_id, source=post.source, labeled_at=labeled_at,
                           note=_optional(form["note"]), extraction=extraction)
    except ValidationError as error:
        raise ValueError(_explain(error)) from None


def form_from_label(label: LabeledPost) -> dict:
    """The reverse of :func:`build_label`, used to show an existing label."""
    e = label.extraction
    return {
        "is_opportunity": e.is_opportunity, "company": e.company or "",
        "remote_policy": e.remote_policy, "remote_scope": e.remote_scope or "",
        "locations": "\n".join(e.locations), "employment_types": list(e.employment_types),
        "visa_sponsorship": e.visa_sponsorship, "language_required": ", ".join(e.language_required),
        "apply_method": e.apply_method, "apply_target": e.apply_target or "",
        "deadline": e.deadline.isoformat() if e.deadline else "",
        "roles": format_roles(e.roles), "note": label.note or "",
    }


def load_labels(path: Path) -> dict[tuple[str, int], LabeledPost]:
    """Load saved labels, keyed by ``(source, post_id)``. Empty if no file yet."""
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        labels = [LabeledPost.model_validate_json(line) for line in f if line.strip()]
    return {(label.source, label.post_id): label for label in labels}


def save_label(path: Path, label: LabeledPost) -> None:
    """Add a label, or replace the earlier label of the same post."""
    labels = load_labels(path)
    labels[(label.source, label.post_id)] = label       # keeps its original position if it existed
    _write_lines(path, [label.model_dump_json() for label in labels.values()])


class LabelSession:
    """The labeling logic, kept apart from the web page so it can be tested."""

    def __init__(self, queue: list[tuple[RawPost, str]], labeled_path: Path) -> None:
        self.queue = queue
        self.labeled_path = labeled_path

    def first_unlabeled(self) -> int:
        """Index of the first post without a label (the last post if all are done)."""
        done = load_labels(self.labeled_path)
        for i, (post, _) in enumerate(self.queue):
            if _key(post) not in done:
                return i
        return len(self.queue) - 1

    def view(self, index: int) -> dict:
        """Everything the page shows for the post at ``index``."""
        index = max(0, min(index, len(self.queue) - 1))
        post, _ = self.queue[index]            # the reason is deliberately not shown
        done = load_labels(self.labeled_path)
        existing = done.get(_key(post))
        form = form_from_label(existing) if existing else dict(DEFAULT_FORM)
        progress = f"**Post {index + 1} of {len(self.queue)}**  |  labeled {len(done)} of {len(self.queue)}"
        if existing:
            progress += "  |  *already labeled (saving again replaces it)*"
        return {"index": index, "progress": progress,
                "link": f"[Open the original post]({post.url})", "text": post.text, "form": form}

    def save(self, index: int, form: dict) -> tuple[bool, str]:
        """Validate and save the label for ``index``. Returns ``(ok, message)``."""
        post, _ = self.queue[index]
        try:
            label = build_label(post, form)
        except ValueError as error:
            return False, f"Not saved: {error}"
        save_label(self.labeled_path, label)
        return True, "Saved."


# --------------------------------------------------------------------------- #
# Part 3: the web page
# --------------------------------------------------------------------------- #

def build_app(session: LabelSession):
    """Build the Gradio page. Imported here so ``select`` works without gradio."""
    import gradio as gr

    with gr.Blocks(title="Label posts") as demo:
        index = gr.State(0)
        progress = gr.Markdown()
        with gr.Row():
            with gr.Column(scale=3):
                link = gr.Markdown()
                text = gr.Textbox(label="Post", lines=30, max_lines=30, interactive=False)
            with gr.Column(scale=2):
                is_opportunity = gr.Checkbox(label="This post advertises an opportunity", value=True)
                company = gr.Textbox(label="Company")
                remote_policy = gr.Radio(["remote", "hybrid", "onsite", "unclear"], label="Remote policy", value="unclear")
                remote_scope = gr.Textbox(label="Remote scope, as written (e.g. US only)")
                locations = gr.Textbox(label="Locations, one per line", lines=2)
                employment_types = gr.CheckboxGroup(["full-time", "part-time", "contract", "internship"], label="Employment types")
                visa = gr.Radio(["yes", "no", "unclear"], label="Visa sponsorship", value="unclear")
                languages = gr.Textbox(label="Languages required (human languages), comma separated")
                apply_method = gr.Radio(["url", "email", "other", "unclear"], label="How to apply", value="unclear")
                apply_target = gr.Textbox(label="Link, email or instruction to apply")
                deadline = gr.Textbox(label="Deadline (YYYY-MM-DD), only if stated")
                roles = gr.Textbox(
                    label="Roles, one per line:  title | location | min | max | currency | period | skills",
                    lines=5,
                    placeholder="Senior Engineer | San Francisco, CA | 150000 | 200000 | USD | year | Python, Go",
                )
                note = gr.Textbox(label="Note (any doubt about this post)")
                status = gr.Markdown()
                with gr.Row():
                    back = gr.Button("Previous")
                    skip = gr.Button("Next without saving")
                    save = gr.Button("Save and next", variant="primary")

        fields = [is_opportunity, company, remote_policy, remote_scope, locations,
                  employment_types, visa, languages, apply_method, apply_target,
                  deadline, roles, note]
        outputs = [index, progress, link, text, *fields, status]

        def show(i: int, message: str = ""):
            v = session.view(i)
            return [v["index"], v["progress"], v["link"], v["text"],
                    *[v["form"][name] for name in FIELDS], message]

        def start():
            return show(session.first_unlabeled())

        def go(i: int, step: int):
            return show(i + step)

        def no_change():
            # "leave this component as it is": gr.skip() in newer Gradio, gr.update() in older
            return gr.skip() if hasattr(gr, "skip") else gr.update()

        def save_and_next(i: int, *values):
            ok, message = session.save(i, dict(zip(FIELDS, values)))
            if not ok:
                return [i, no_change(), no_change(), no_change(), *[no_change() for _ in fields], message]
            if i + 1 >= len(session.queue):
                return show(i, "Saved. That was the last post.")
            return show(i + 1, "Saved.")

        demo.load(start, None, outputs, api_name="start")
        back.click(lambda i: go(i, -1), [index], outputs, api_name="previous")
        skip.click(lambda i: go(i, 1), [index], outputs, api_name="skip")
        save.click(save_and_next, [index, *fields], outputs, api_name="save")
    return demo


# --------------------------------------------------------------------------- #
# Command line
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    """Run ``select`` or ``app`` from the command line."""
    parser = argparse.ArgumentParser(description="Choose posts to hand-label, and label them.")
    sub = parser.add_subparsers(dest="command", required=True)

    pick = sub.add_parser("select", help="choose posts that cover the hard cases")
    pick.add_argument("--n", type=int, default=50, help="how many posts (default 50)")
    pick.add_argument("--seed", type=int, default=7, help="random seed (default 7)")
    pick.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    pick.add_argument("--out", type=Path, default=DEFAULT_TO_LABEL)

    app = sub.add_parser("app", help="open the labeling app in the browser")
    app.add_argument("--to-label", type=Path, default=DEFAULT_TO_LABEL)
    app.add_argument("--labeled", type=Path, default=DEFAULT_LABELED)

    args = parser.parse_args(argv)

    if args.command == "select":
        if args.out.exists():
            print(f"{args.out} already exists. Delete it first if you want a new selection "
                  "(labels already saved in labeled.jsonl are kept either way).", file=sys.stderr)
            return 1
        pairs = select_posts(load_raw_posts(args.raw), n=args.n, seed=args.seed)
        write_selection(pairs, args.out)
        counts: dict[str, int] = defaultdict(int)
        for _, reason in pairs:
            counts[reason] += 1
        print(f"Chose {len(pairs)} posts -> {args.out}")
        for reason, count in sorted(counts.items(), key=lambda item: -item[1]):
            print(f"  {reason:20s} {count}")
        return 0

    if not args.to_label.exists():
        print(f"{args.to_label} not found. Run `python label.py select` first.", file=sys.stderr)
        return 1
    session = LabelSession(load_queue(args.to_label), args.labeled)
    build_app(session).launch()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())