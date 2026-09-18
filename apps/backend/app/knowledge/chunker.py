import re


def chunk_markdown(text: str, max_chars: int = 800) -> list[str]:
    stripped = text.strip()
    lines = stripped.split("\n", 1)
    if lines[0].startswith("# "):
        body = lines[1] if len(lines) > 1 else ""
    else:
        body = stripped
    sections = re.split(r"\n(?=## )", body)

    chunks: list[str] = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        if len(section) <= max_chars:
            chunks.append(section)
        else:
            chunks.extend(_split_by_paragraphs(section, max_chars))
    return chunks


def _split_by_paragraphs(section: str, max_chars: int) -> list[str]:
    paragraphs = [p.strip() for p in section.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) > max_chars and current:
            chunks.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks
