from __future__ import annotations

from app.domain.services.categorization import MatchRule, match_category, normalize_text


def test_user_rule_beats_builtin():
    rules = [
        MatchRule("星巴克", 1, is_builtin=True),
        MatchRule("星巴克", 2, is_builtin=False),
    ]
    assert match_category("星巴克(国贸店)", rules) == 2


def test_longer_keyword_wins_inside_same_tier():
    rules = [
        MatchRule("星巴克", 1, is_builtin=True),
        MatchRule("星巴克臻选", 3, is_builtin=True),
    ]
    assert match_category("星巴克臻选上海烘焙工坊", rules) == 3


def test_priority_wins_inside_same_tier():
    rules = [
        MatchRule("咖啡", 1, is_builtin=False, priority=0),
        MatchRule("咖啡", 9, is_builtin=False, priority=5),
    ]
    assert match_category("manner 咖啡", rules) == 9


def test_no_match_returns_none():
    assert match_category("某个不认识的商户", [MatchRule("星巴克", 1)]) is None
    assert match_category("", [MatchRule("星巴克", 1)]) is None


def test_full_width_and_case_normalization():
    assert normalize_text("ＳＴＡＲＢＵＣＫＳ") == "starbucks"
    assert match_category("ＳＴＡＲＢＵＣＫＳ 咖啡", [MatchRule("starbucks", 7)]) == 7
