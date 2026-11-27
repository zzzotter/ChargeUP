"""领域层依赖检查（SRS 5.3）：domain 不得 import 数据库/框架。

用法：python -m tools.domain_purity  或  python scripts/check_domain_purity.py
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

FORBIDDEN_ROOTS = {
    "sqlalchemy",
    "fastapi",
    "starlette",
    "pydantic",
    "alembic",
    "psycopg",
    "psycopg2",
    "pgvector",
    "uvicorn",
}

FORBIDDEN_APP_PREFIXES = (
    "app.infrastructure",
    "app.interfaces",
    "app.application",
)


def _forbidden(module: str) -> bool:
    root = module.split(".", 1)[0]
    if root in FORBIDDEN_ROOTS:
        return True
    return any(module == prefix or module.startswith(f"{prefix}.") for prefix in FORBIDDEN_APP_PREFIXES)


def check_file(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    problems: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _forbidden(alias.name):
                    problems.append(f"{path}:{node.lineno} 禁止导入 {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                continue  # 相对导入只可能指向 domain 自身
            module = node.module or ""
            if _forbidden(module):
                problems.append(f"{path}:{node.lineno} 禁止从 {module} 导入")
    return problems


def check_domain(domain_dir: Path) -> list[str]:
    problems: list[str] = []
    for path in sorted(domain_dir.rglob("*.py")):
        problems.extend(check_file(path))
    return problems


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    domain_dir = root / "app" / "domain"
    problems = check_domain(domain_dir)
    if problems:
        print("领域层依赖检查未通过：")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(f"领域层依赖检查通过（{domain_dir}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
