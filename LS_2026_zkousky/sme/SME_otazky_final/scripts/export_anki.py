#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "main.tex"
OUT_DIR = ROOT / "anki_export"
MEDIA_DIR = OUT_DIR / "media"


SECTION_RE = re.compile(r"\\section\*\{")
QUESTION_START = r"\begin{tcolorbox}[title={\stepcounter{questionnumber}\thequestionnumber. "
BOX_START_RE = re.compile(
    r"\\begin\{(?P<env>tcolorbox|examplebox|addonbox)\}(?:\[(?P<opt>.*?)\])?",
    re.DOTALL,
)


def extract_braced(text: str, start: int, open_char: str = "{", close_char: str = "}") -> tuple[str, int]:
    assert text[start] == open_char
    depth = 0
    i = start
    while i < len(text):
        ch = text[i]
        if ch == open_char:
            depth += 1
        elif ch == close_char:
            depth -= 1
            if depth == 0:
                return text[start + 1 : i], i + 1
        i += 1
    raise ValueError(f"Unclosed block starting at {start}")


def find_matching_env_end(text: str, start: int, env_name: str) -> int:
    begin_token = f"\\begin{{{env_name}}}"
    end_token = f"\\end{{{env_name}}}"
    depth = 1
    i = start
    while i < len(text):
        next_begin = text.find(begin_token, i)
        next_end = text.find(end_token, i)
        if next_end == -1:
            raise ValueError(f"Missing {end_token}")
        if next_begin != -1 and next_begin < next_end:
            depth += 1
            i = next_begin + len(begin_token)
            continue
        depth -= 1
        if depth == 0:
            return next_end
        i = next_end + len(end_token)
    raise ValueError(f"Missing closing env for {env_name}")


def parse_sections(text: str) -> list[tuple[int, str, int, int]]:
    sections = []
    matches = list(SECTION_RE.finditer(text))
    for idx, match in enumerate(matches):
        title, after = extract_braced(text, match.end() - 1)
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        sections.append((idx + 1, title.strip(), start, end))
    return sections


def parse_box_title(env: str, opt: str | None, card_id: str) -> str:
    if env == "tcolorbox":
        if not opt:
            return card_id
        prefix = r"title={\stepcounter{questionnumber}\thequestionnumber. "
        start = opt.find(prefix)
        if start != -1:
            start += len(prefix)
            end = opt.rfind("}")
            if end != -1 and end >= start:
                return opt[start:end].strip()
        title_match = re.search(r"title\s*=\s*\{(.*)\}\s*$", opt, re.DOTALL)
        if title_match:
            return title_match.group(1).strip()
        title_match = re.search(r"title\s*=\s*(.+?)\s*$", opt, re.DOTALL)
        if title_match:
            return title_match.group(1).strip()
        return card_id

    title_match = re.search(r"title=\{(.*)\}", opt or "", re.DOTALL)
    if title_match:
        return title_match.group(1).strip()
    return card_id


def parse_questions(text: str, sections: list[tuple[int, str, int, int]]) -> list[dict[str, str]]:
    cards = []
    for chapter_number, section_title, sec_start, sec_end in sections:
        chunk = text[sec_start:sec_end]
        idx = 0
        question_number = 0
        example_number = 0
        addon_number = 0
        while True:
            match = BOX_START_RE.search(chunk, idx)
            if not match:
                break
            env = match.group("env")
            opt = match.group("opt")
            body_start = match.end()
            abs_body_start = sec_start + body_start
            body_end = find_matching_env_end(text, abs_body_start, env)
            body = text[abs_body_start:body_end].strip()
            idx = body_end - sec_start + len(fr"\end{{{env}}}")

            if env == "tcolorbox":
                question_number += 1
                card_id = f"{chapter_number}.{question_number}"
                card_type = "question"
            elif env == "examplebox":
                example_number += 1
                card_id = f"{chapter_number}.E{example_number}"
                card_type = "example"
            else:
                addon_number += 1
                card_id = f"{chapter_number}.A{addon_number}"
                card_type = "addon"

            raw_title = parse_box_title(env, opt, card_id)
            cards.append(
                {
                    "chapter_number": str(chapter_number),
                    "chapter_title": section_title,
                    "question_number": str(question_number),
                    "card_id": card_id,
                    "card_type": card_type,
                    "title": raw_title,
                    "body": body,
                }
            )
    return cards


def strip_outer_whitespace(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def normalize_title(title: str, card_id: str) -> str:
    cleaned = title.strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return f"{card_id}. {cleaned}"


def latex_inline_to_mathjax(text: str) -> str:
    parts = re.split(r"(\$[^$]+\$)", text)
    out = []
    for part in parts:
        if len(part) >= 2 and part.startswith("$") and part.endswith("$"):
            out.append(rf"\({part[1:-1]}\)")
        else:
            out.append(part)
    return "".join(out)


def escape_non_tag_angles(text: str) -> str:
    return re.sub(
        r"<(?!/?(?:div|strong|em|code|ol|ul|li|img|br|hr)\b)",
        "&lt;",
        text,
    )


def replace_text_macros(text: str) -> str:
    patterns = [
        (r"\\textbf\{([^{}]*)\}", r"<strong>\1</strong>"),
        (r"\\textit\{([^{}]*)\}", r"<em>\1</em>"),
        (r"\\texttt\{([^{}]*)\}", r"<code>\1</code>"),
        (r"\\mathrm\{([^{}]*)\}", r"\\mathrm{\1}"),
        (r"\\Omega", r"\\Omega"),
    ]
    updated = text
    while True:
        prev = updated
        for pattern, repl in patterns:
            updated = re.sub(pattern, repl, updated)
        if updated == prev:
            return updated


def convert_iffileexists(block: str) -> str:
    pattern = re.compile(
        r"\\IfFileExists\{([^}]+)\}\s*\{\\includegraphics\[[^]]*\]\{([^}]+)\}\}\s*\{[^{}]*\}",
        re.DOTALL,
    )
    return pattern.sub(r"\\includegraphics{\2}", block)


def convert_figures(text: str) -> tuple[str, set[str]]:
    used_images: set[str] = set()
    figure_re = re.compile(r"\\begin\{figure\}\[H\](.*?)\\end\{figure\}", re.DOTALL)

    def repl(match: re.Match[str]) -> str:
        block = convert_iffileexists(match.group(1))
        img_match = re.search(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", block, re.DOTALL)
        cap_match = re.search(r"\\caption\{([^}]+)\}", block, re.DOTALL)
        if not img_match:
            return ""
        image_path = img_match.group(1).strip()
        filename = Path(image_path).name
        used_images.add(image_path)
        caption = cap_match.group(1).strip() if cap_match else ""
        caption_html = f'<div class="caption">{html.escape(caption)}</div>' if caption else ""
        return f'<div class="figure"><img src="{html.escape(filename)}">{caption_html}</div>'

    return figure_re.sub(repl, text), used_images


def convert_lists(text: str) -> str:
    def convert_env(name: str, tag: str, source: str) -> str:
        env_re = re.compile(rf"\\begin\{{{name}\}}(.*?)\\end\{{{name}\}}", re.DOTALL)

        def repl(match: re.Match[str]) -> str:
            inner = match.group(1).strip()
            parts = re.split(r"\\item\s*", inner)
            items = [part.strip() for part in parts[1:] if part.strip()]
            rendered = "".join(f"<li>{item}</li>" for item in items)
            return f"<{tag}>{rendered}</{tag}>"

        return env_re.sub(repl, source)

    text = convert_env("enumerate", "ol", text)
    text = convert_env("itemize", "ul", text)
    return text


def cleanup_latex(text: str) -> str:
    text = strip_outer_whitespace(text)
    text = text.replace("\\centering", "")
    text = re.sub(r"\\label\{[^}]*\}", "", text)
    text = re.sub(r"(?m)^\s*%\s.*$", "", text)
    text = convert_lists(text)
    text = text.replace("\\\\", "<br>\n")
    text = replace_text_macros(text)
    text = latex_inline_to_mathjax(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\n", "<br>\n", text)
    text = re.sub(r"(<br>\s*){2,}", "<br><br>\n", text)
    text = re.sub(r"\s*\n\s*", " ", text).strip()
    return escape_non_tag_angles(text)


def render_front(card: dict[str, str]) -> str:
    title = normalize_title(card["title"], card["card_id"])
    section = html.escape(card["chapter_title"])
    front = (
        f'<div class="section">{section}</div>'
        f'<div class="question">{latex_inline_to_mathjax(title)}</div>'
    )
    return escape_non_tag_angles(front)


def render_back(card: dict[str, str]) -> tuple[str, set[str]]:
    body, images = convert_figures(card["body"])
    answer = cleanup_latex(body)
    return answer, images


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def copy_media(image_paths: set[str]) -> None:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    for image_path in sorted(image_paths):
        src = ROOT / image_path
        if not src.exists():
            continue
        shutil.copy2(src, MEDIA_DIR / src.name)


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    sections = parse_sections(text)
    cards = parse_questions(text, sections)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    used_images: set[str] = set()
    for card in cards:
        front = render_front(card)
        back, images = render_back(card)
        used_images.update(images)
        tags = " ".join(
            [
                "sme",
                f"chapter_{card['chapter_number']}",
                f"type_{card['card_type']}",
                slugify(card["chapter_title"]),
            ]
        )
        rows.append((front, back, tags))

    with (OUT_DIR / "notes.tsv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
        writer.writerows(rows)

    copy_media(used_images)

    media_list = "\n".join(sorted(Path(path).name for path in used_images))
    (OUT_DIR / "media_files.txt").write_text(media_list + ("\n" if media_list else ""), encoding="utf-8")


if __name__ == "__main__":
    main()
