from pydantic import BaseModel


class FaithfulnessVerdict(BaseModel):
    is_faithful: bool
    unsupported_claims: list[str]
