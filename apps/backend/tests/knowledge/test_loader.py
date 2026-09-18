from pathlib import Path

from app.knowledge.loader import load_documents


def test_loads_markdown_files_with_category_from_parent_dir(tmp_path: Path):
    billing_dir = tmp_path / "billing"
    billing_dir.mkdir()
    (billing_dir / "billing_faq.md").write_text("# Billing FAQ\n\ncontent")

    refunds_dir = tmp_path / "refunds"
    refunds_dir.mkdir()
    (refunds_dir / "refund_policy.md").write_text("# Refund Policy\n\ncontent")

    documents = load_documents(tmp_path)

    assert len(documents) == 2
    by_name = {doc.document: doc for doc in documents}
    assert by_name["billing_faq.md"].category == "billing"
    assert by_name["refund_policy.md"].category == "refunds"


def test_ignores_non_markdown_files(tmp_path: Path):
    category_dir = tmp_path / "billing"
    category_dir.mkdir()
    (category_dir / "billing_faq.md").write_text("# Billing FAQ\n\ncontent")
    (category_dir / "notes.txt").write_text("not markdown")

    documents = load_documents(tmp_path)

    assert len(documents) == 1
    assert documents[0].document == "billing_faq.md"


def test_returns_empty_list_for_empty_directory(tmp_path: Path):
    assert load_documents(tmp_path) == []
