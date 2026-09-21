import asyncio
import sys

from app.agents.dependencies import get_classifier_agent, get_response_agent
from app.db.session import session_scope


async def main() -> None:
    message = " ".join(sys.argv[1:]) or (
        "I was charged twice for my subscription this month and I want a refund."
    )

    classifier = get_classifier_agent()
    classification = await classifier.classify(message)
    print("Classification:")
    print(classification.model_dump_json(indent=2))
    print()

    responder = get_response_agent()
    async with session_scope() as session:
        response = await responder.respond(session, message)

    print("Response:")
    print(f"  grounded: {response.grounded}")
    print(f"  sources:  {response.sources}")
    print(f"  answer:   {response.answer}")


if __name__ == "__main__":
    asyncio.run(main())
