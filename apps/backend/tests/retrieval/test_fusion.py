from app.retrieval.fusion import fuse_and_rank, reciprocal_rank_fusion


def test_single_ranking_scores_are_monotonically_decreasing():
    scores = reciprocal_rank_fusion([["a", "b", "c"]], k=60)

    assert scores["a"] > scores["b"] > scores["c"]


def test_first_rank_score_matches_formula():
    scores = reciprocal_rank_fusion([["a"]], k=60)

    assert scores["a"] == 1.0 / 61


def test_item_in_both_rankings_scores_higher_than_single_ranking_item():
    scores = reciprocal_rank_fusion([["a", "b"], ["a", "c"]], k=60)

    assert scores["a"] > scores["b"]
    assert scores["a"] > scores["c"]


def test_items_appear_even_if_only_in_one_ranking():
    scores = reciprocal_rank_fusion([["a"], ["b"]], k=60)

    assert "a" in scores
    assert "b" in scores


def test_fuse_and_rank_sorts_descending():
    ranked = fuse_and_rank([["a", "b", "c"]], k=60)

    assert [item_id for item_id, _ in ranked] == ["a", "b", "c"]
