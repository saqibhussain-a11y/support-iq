import asyncio
import sys

from app.db.session import session_scope
from app.workflows.dependencies import get_support_workflow_service


async def main() -> None:
    message = " ".join(sys.argv[1:]) or "hey"

    service = get_support_workflow_service()
    async with session_scope() as session:
        result = await service.run(session, message)

    print("Classification:")
    print(result["classification"].model_dump_json(indent=2))
    print()
    print("Response:")
    print(f"  grounded: {result['response'].grounded}")
    print(f"  sources:  {result['response'].sources}")
    print(f"  answer:   {result['response'].answer}")
    print()
    print("Faithfulness:")
    if result["faithfulness"] is None:
        print("  skipped (not a grounded answer)")
    else:
        print(f"  is_faithful:        {result['faithfulness'].is_faithful}")
        print(f"  unsupported_claims: {result['faithfulness'].unsupported_claims}")
    print()
    print("Escalation:")
    print(f"  level:   {result['escalation'].value}")
    print(f"  reasons: {result['escalation_reasons']}")


if __name__ == "__main__":
    asyncio.run(main())
