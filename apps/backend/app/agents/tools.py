TOOL_SPECS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Search the support knowledge base for policy chunks relevant to a query. "
                "Use this for most questions, including when you need to look something up "
                "more than once with a refined query."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "A focused search query"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_full_document",
            "description": (
                "Fetch the complete text of a specific knowledge base document by filename, "
                "e.g. 'refund_policy.md'. Use this when you already know exactly which "
                "document has the answer and need the full policy rather than a fragment."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "document_name": {"type": "string", "description": "Exact document filename"},
                },
                "required": ["document_name"],
            },
        },
    },
]
