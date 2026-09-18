from pathlib import Path

from app.knowledge.schemas import RawDocument


def load_documents(root: Path) -> list[RawDocument]:
    documents = []
    for path in sorted(root.rglob("*.md")):
        category = path.parent.name
        documents.append(
            RawDocument(
                document=path.name,
                category=category,
                text=path.read_text(encoding="utf-8"),
            )
        )
    return documents
