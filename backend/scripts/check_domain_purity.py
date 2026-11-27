"""CI 入口：校验领域层未依赖框架（可作为 pre-commit / CI 步骤）。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.domain_purity import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
