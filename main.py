#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главный модуль запуска приложения GigaChat Agent.
"""

import subprocess
import sys
import os
import uvicorn

def install_requirements():
    """Установит зависимости из requirements.txt если они не установлены."""
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
    install_requirements()
    uvicorn.run("src.web.server:app", host="127.0.0.1", port=8010, reload=True, log_level="info")
