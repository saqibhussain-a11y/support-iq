import asyncio
import sys

from app.db.session import session_scope
from app.retrieval.dependencies import get_retrieval_service


async def main() -> None:
    query = " ".join(sys.argv[1:]) or "Can I get a refund for a duplicate subscription charge?"
    service = get_retrieval_service()

    async with session_scope() as session:
        result = await service.search(session, query)

    print(f"Query: {result.query}\n")
    for rank, chunk in enumerate(result.chunks, start=1):
        print(f"{rank}. {chunk.document} [{chunk.category}] chunk #{chunk.chunk_index}")
        print(f"   fused_score={chunk.fused_score:.4f}  rerank_score={chunk.rerank_score:.4f}")
        print(f"   {chunk.content[:120].replace(chr(10), ' ')}...")
        print()


if __name__ == "__main__":
    asyncio.run(main())
