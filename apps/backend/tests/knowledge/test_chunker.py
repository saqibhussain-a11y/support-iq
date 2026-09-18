from app.knowledge.chunker import chunk_markdown


def test_splits_on_h2_headings():
    text = (
        "# Title\n\n"
        "## First Section\n\nSome content here.\n\n"
        "## Second Section\n\nMore content here."
    )

    chunks = chunk_markdown(text)

    assert chunks == [
        "## First Section\n\nSome content here.",
        "## Second Section\n\nMore content here.",
    ]


def test_drops_the_leading_h1_title():
    text = "# Title\n\n## Only Section\n\nBody text."

    chunks = chunk_markdown(text)

    assert len(chunks) == 1
    assert "# Title" not in chunks[0]


def test_splits_oversized_section_by_paragraph():
    long_section = "## Big Section\n\n" + "\n\n".join(f"Paragraph {i} " * 10 for i in range(5))
    text = f"# Title\n\n{long_section}"

    chunks = chunk_markdown(text, max_chars=100)

    assert len(chunks) > 1
    assert all(len(chunk) <= 200 for chunk in chunks)


def test_extra_blank_lines_do_not_produce_empty_chunks():
    text = "# Title\n\n## Section One\n\nContent one.\n\n\n\n## Section Two\n\nContent two."

    chunks = chunk_markdown(text)

    assert len(chunks) == 2
    assert all(chunk for chunk in chunks)
