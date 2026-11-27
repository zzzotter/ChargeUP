"""第 11 天检查（三）：领域层不依赖任何 Web/DB 框架。"""
from tools.domain_purity import check_domain


def test_real_domain_layer_is_pure(backend_path):
    domain_dir = backend_path / "app" / "domain"
    problems = check_domain(domain_dir)
    assert problems == [], "领域层不得依赖框架：\n" + "\n".join(problems)


def test_checker_detects_violation(tmp_path):
    (tmp_path / "bad.py").write_text(
        "import sqlalchemy\nfrom app.infrastructure import models\n", encoding="utf-8"
    )
    assert len(check_domain(tmp_path)) == 2
