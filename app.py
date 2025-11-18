#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import sys
import os

def _install_dependency() -> None:
    """
    Установит зависимости из requirements.txt если они не установлены.
    """
    requirements_file = os.path.join(os.path.dirname(__file__), "requirements.txt")

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

if __name__ == "__main__":
    _install_dependency()
    from src.main import main
    import asyncio
    asyncio.run(main())

