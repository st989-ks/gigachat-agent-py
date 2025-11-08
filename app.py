#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import sys
import os
import asyncio
from src.main import main


def _install_dependency():
    """
    Установит зависимости из requirements.txt если они не установлены.
    """
    requirements_file = os.path.join(os.path.dirname(__file__), "requirements.txt")

    if not os.path.exists(requirements_file):
        print(f"⚠️  Файл {requirements_file} не найден")
        return

    print("📦 Проверка зависимостей...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", requirements_file],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            print("✅ Зависимости успешно установлены")
        else:
            print("⚠️  Ошибка при установке зависимостей:")
            print(result.stderr)
            sys.exit(1)

    except subprocess.TimeoutExpired:
        print("❌ Установка зависимостей заняла слишком много времени")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка при установке зависимостей: {e}")
        sys.exit(1)


if __name__ == "__main__":
    _install_dependency()
    asyncio.run(main())
