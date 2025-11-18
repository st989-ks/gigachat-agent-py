#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
make_structure.py — модуль для сбора структуры проекта и его содержимого в текст.
"""

import os
from fnmatch import fnmatch

# === 1. Внутренние пути, которые всегда игнорируются ===
INTERNAL_IGNORE = [
    ".git",
    ".idea",
    "__pycache__",
    "venv",
    "env",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    "structure-for-llm.txt",
    "*.pyc",
    "*.pyo",
]


# === 2. Загрузка .gitignore ===
def load_gitignore_patterns(root: str):# type: ignore
    """Возвращает список паттернов из .gitignore (если есть)."""
    path = os.path.join(root, ".gitignore")
    if not os.path.exists(path):
        return []
    patterns = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            patterns.append(line)
    return patterns


# === 3. Проверка на игнорирование ===
def should_ignore(path: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        if fnmatch(os.path.basename(path), pattern) or fnmatch(path, pattern):
            return True
    return False


# === 4. Сбор файлов ===
def collect_files(root: str, ignore_patterns: list[str]):  # type: ignore
    result = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir == ".":
            rel_dir = ""

        # фильтруем каталоги
        dirnames[:] = [
            d for d in dirnames
            if not should_ignore(os.path.join(rel_dir, d), ignore_patterns)
        ]

        # добавляем файлы
        for name in filenames:
            rel_path = os.path.join(rel_dir, name)
            if should_ignore(rel_path, ignore_patterns):
                continue
            result.append(rel_path)

    return sorted(result)


# === 5. Строим дерево ===
def build_tree(root: str, ignore_patterns: list[str]) -> str:
    lines = []

    def walk(path, prefix=""): # type: ignore
        entries = sorted(os.listdir(path))
        for i, name in enumerate(entries):
            rel_path = os.path.relpath(os.path.join(path, name), root)
            if should_ignore(rel_path, ignore_patterns):
                continue
            connector = "└── " if i == len(entries) - 1 else "├── "
            lines.append(f"{prefix}{connector}{name}")
            if os.path.isdir(os.path.join(path, name)):
                new_prefix = prefix + ("    " if i == len(entries) - 1 else "│   ")
                walk(os.path.join(path, name), new_prefix)

    lines.append(os.path.basename(root) + "/")
    walk(root)
    return "\n".join(lines)


# === 6. Чтение файлов ===
def read_file_content(path: str):# type: ignore
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except (UnicodeDecodeError, PermissionError, OSError):
        return None


# === 7. Основная функция: сбор текста ===
def collect_project_text(root: str) -> str:
    """Возвращает строку с деревом проекта и текстом всех файлов."""
    root = os.path.abspath(root)
    gitignore_patterns = load_gitignore_patterns(root)

    # совмещаем внутренние и gitignore паттерны
    ignore_patterns = gitignore_patterns + INTERNAL_IGNORE

    files = collect_files(root, ignore_patterns)
    tree = build_tree(root, ignore_patterns)

    parts = ["## Структура проекта\n", tree, "\n\n---\n\n## Содержимое файлов\n"]

    for rel in files:
        full = os.path.join(root, rel)
        content = read_file_content(full)
        parts.append(f"\n--- {rel} ---\n")
        if content is None:
            parts.append("[Не удалось прочитать файл]\n")
        else:
            parts.append(content)
            if not content.endswith("\n"):
                parts.append("\n")

    return "".join(parts)
