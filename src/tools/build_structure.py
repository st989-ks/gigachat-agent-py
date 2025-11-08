#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
build_structure.py — создаёт файл structure-for-llm.txt с содержимым проекта.
"""

import os
import sys

from src.tools.make_structure import collect_project_text

OUTPUT_FILENAME = "data/structure-for-llm.txt"


def main()-> None:
    root = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()
    output_path = os.path.join(root, OUTPUT_FILENAME)

    print(f"📁 Сканирование проекта: {root}")

    text = collect_project_text(root)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"✅ Файл создан: {output_path}")


if __name__ == "__main__":
    main()
