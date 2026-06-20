"""Запуск QuizAIr для Telegram: бэкенд + публичный туннель + авто-настройка бота.

Читает TG_BOT_TOKEN из файла .env (НЕ из аргументов/чата) и автоматически
прописывает Mini App в кнопку меню бота на текущий адрес туннеля.

Бесплатный туннель (localhost.run) иногда обрывается — скрипт это отслеживает,
сам переподнимает туннель и заново перенастраивает бота на новый адрес.

Запуск:  start-telegram.bat
Останов: Ctrl+C или закрыть окно.
"""
from __future__ import annotations

import json
import re
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
PYTHON = BACKEND / ".venv" / "Scripts" / "python.exe"
SSH_KEY = Path.home() / ".ssh" / "id_ed25519"
PORT = 8080
MENU_TEXT = "🎮 Играть"
URL_RE = re.compile(r"https://[a-z0-9-]+\.lhr\.life")


def load_token() -> str:
    for env in (ROOT / ".env", BACKEND / ".env"):
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                s = line.strip()
                if s.startswith("TG_BOT_TOKEN") and "=" in s:
                    return s.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def set_menu_button(token: str, url: str) -> dict:
    api = f"https://api.telegram.org/bot{token}/setChatMenuButton"
    payload = json.dumps(
        {"menu_button": {"type": "web_app", "text": MENU_TEXT, "web_app": {"url": url}}}
    ).encode("utf-8")
    req = urllib.request.Request(
        api, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def wait_backend(timeout: int = 40) -> bool:
    """Опрашивает /health, пока бэкенд не ответит (он дольше стартует из-за сида)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{PORT}/health", timeout=3
            ) as r:
                if r.status == 200:
                    return True
        except Exception:  # noqa: BLE001
            time.sleep(1)
    return False


def start_backend():
    print(f"[1/3] Бэкенд на http://localhost:{PORT} ...")
    blog = open(ROOT / "backend.log", "w", encoding="utf-8")
    proc = subprocess.Popen(
        [str(PYTHON), "-m", "uvicorn", "app.main:app", "--port", str(PORT)],
        cwd=str(BACKEND),
        stdout=blog,
        stderr=subprocess.STDOUT,
    )
    if wait_backend():
        print("      бэкенд готов.")
    else:
        print("      [!] бэкенд не ответил за 40с — смотри backend.log")
    return proc, blog


def start_tunnel():
    """Поднимает ssh-туннель, ждёт публичный URL. Возвращает (proc, url).

    С SSH-ключом + зарегистрированным аккаунтом localhost.run адрес постоянный.
    Без ключа — случайный адрес (но тоже без заглушки).
    """
    cmd = [
        "ssh", "-R", f"80:localhost:{PORT}",
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "ServerAliveInterval=20",
        "-o", "ServerAliveCountMax=3",
        "-o", "ExitOnForwardFailure=yes",
    ]
    if SSH_KEY.exists():
        cmd += ["-i", str(SSH_KEY), "localhost.run"]
    else:
        cmd += ["nokey@localhost.run"]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    deadline = time.time() + 45
    while time.time() < deadline:
        line = proc.stdout.readline() if proc.stdout else ""
        if not line:
            if proc.poll() is not None:
                return proc, None
            continue
        m = URL_RE.search(line)
        if m:
            return proc, m.group(0)
    return proc, None


def main() -> None:
    print("=" * 60)
    print("  QuizAIr  ->  Telegram   (self-healing)")
    print("=" * 60)
    token = load_token()
    if not token:
        print("[!] TG_BOT_TOKEN не найден в .env — кнопку меню настрою НЕ смогу.")
        print("    Создай miniAPP\\.env со строкой  TG_BOT_TOKEN=токен_от_BotFather")
        print("    Адрес туннеля буду показывать — вставляй в @BotFather вручную.\n")

    backend, blog = start_backend()
    last_url = None
    try:
        while True:
            print("[2/3] Поднимаю туннель (localhost.run)...")
            tunnel, url = start_tunnel()
            if not url:
                print("    [!] Туннель не поднялся. Повтор через 5 сек...")
                try:
                    tunnel.terminate()
                except Exception:  # noqa: BLE001
                    pass
                time.sleep(5)
                continue

            print("\n" + "-" * 60)
            print(f"  Публичный адрес:  {url}")
            print("-" * 60)
            if token and url != last_url:
                print("[3/3] Настраиваю кнопку меню бота...")
                try:
                    res = set_menu_button(token, url)
                    if res.get("ok"):
                        print("    OK! Открой бота -> кнопка меню снизу слева.")
                        print("    (если апп уже открыт — закрой вкладку и открой заново)")
                    else:
                        print(f"    [!] Telegram ошибка: {res}")
                except Exception as e:  # noqa: BLE001
                    print(f"    [!] Не настроил автоматически: {e}")
            elif not token:
                print("    Вставь адрес выше в @BotFather (Menu Button).")
            last_url = url
            print("\nРаботает. Не закрывай окно. Ctrl+C — стоп.\n")

            # ждём, пока туннель жив; при обрыве ssh завершится -> переподнимем
            while True:
                line = tunnel.stdout.readline() if tunnel.stdout else ""
                if not line and tunnel.poll() is not None:
                    break
            print("[!] Туннель оборвался — переподключаюсь...\n")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nОстанавливаю...")
    finally:
        try:
            backend.terminate()
        except Exception:  # noqa: BLE001
            pass
        blog.close()


if __name__ == "__main__":
    main()
