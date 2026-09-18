def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> dict[str, float]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, item_id in enumerate(ranking):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank + 1)
    return scores


def fuse_and_rank(rankings: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    scores = reciprocal_rank_fusion(rankings, k)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)
