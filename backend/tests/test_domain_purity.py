from __future__ import annotations

from pathlib import Path

from tools.domain_purity import check_domain

DOMAIN_DIR = Path(__file__).resolve().parents[1] / "app" / "domain"


def test_domain_layer_has_no_framework_imports():
    problems = check_domain(DOMAIN_DIR)
    assert problems == [], "领域层不得依赖数据库或框架：\n" + "\n".join(problems)


def test_checker_detects_violation(tmp_path):
    sample = tmp_path / "bad.py"
    sample.write_text("import sqlalchemy\nfrom app.infrastructure import models\n", encoding="utf-8")
    problems = check_domain(tmp_path)
    assert len(problems) == 2
