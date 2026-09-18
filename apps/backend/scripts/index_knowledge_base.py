import asyncio

from app.core.config import get_settings
from app.db.session import session_scope
from app.embeddings.dependencies import get_embedding_provider
from app.knowledge.indexer import index_knowledge_base


async def main() -> None:
    settings = get_settings()
    embedding_provider = get_embedding_provider()

    async with session_scope() as session:
        result = await index_knowledge_base(session, embedding_provider, settings.knowledge_base_path)

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
