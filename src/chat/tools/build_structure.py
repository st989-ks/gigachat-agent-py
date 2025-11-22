#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.chat.core.configs import settings
from src.chat.tools.make_structure import collect_project_text


def main()-> None:
    root = str(settings.PROJECT_ROOT)
    output_path=settings.DATA_DIR / "structure-for-llm.txt"

    print(f"📁 Сканирование проекта: {root}")

    text = collect_project_text(root)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"✅ Файл создан: {output_path}")


if __name__ == "__main__":
    main()
