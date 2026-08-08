# Точка входа сборки.
#
# Что делает по порядку:
#   1. смотрит, какая версия стоит   (ВЕРСИЯ.txt)
#   2. спрашивает у GitHub, что вышло нового
#   3. если вышло — откладывает старые файлы в сторонку и кладёт новые
#   4. запускает мост Photoshop отдельным окном и следом сам ComfyUI
#
# Откат: launcher.py --откат   (или кнопка ОТКАТ.bat)
# Только запуск, без проверки обновлений: launcher.py --без-обновлений
#
# Здесь только то, что уже есть во встроенном Python. Ничего доставлять
# не нужно — иначе сборка перестанет быть переносимой.
import os, sys, json, time, shutil, zipfile, hashlib, datetime, subprocess
import urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _log; _log.start("launcher")

HERE = os.path.dirname(os.path.abspath(__file__))
VERSION_FILE = os.path.join(HERE, "ВЕРСИЯ.txt")
BACKUP_ROOT = os.path.join(HERE, "бэкап")
# Что откатили — то больше не ставим. Иначе откат бессмысленен: следующий
# же запуск вернул бы то, от чего человек только что избавился.
REJECTED = os.path.join(BACKUP_ROOT, "не_ставить.txt")
PY = os.path.join(HERE, "python_embeded", "python.exe")
# Рассказ автора патча. Показываем его человеку, но на диск не кладём —
# незачем копить их в главной папке.
NOTE_NAME = "ЧТО_ДЕЛАТЬ.txt"

# Откуда берём обновления. Репозиторий открытый, поэтому качается без пароля.
# Адрес можно подменить через переменную окружения POCKET_URL — этим
# проверяют механизм на поддельных обновлениях, не трогая настоящие.
BASE_URL = os.environ.get("POCKET_URL") or \
    "https://raw.githubusercontent.com/dreizehntephantom/comfy-pocket/main/patches/"
INDEX_URL = BASE_URL + "index.json"

# Эти папки патч не трогает никогда: там твои картинки и записи, а не инструмент.
NEVER_TOUCH = ("ComfyUI/output", "ComfyUI/input", "refs", "depth/donor",
               "canny/donor", "logs", "бэкап")


def line(s=""):
    print(s, flush=True)


# ---------------------------------------------------------------- версия

def read_version():
    try:
        return int(open(VERSION_FILE, encoding="utf-8").read().strip() or 0)
    except Exception:
        return 0


def write_version(n):
    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(str(n) + "\n")


def read_rejected():
    """Номера обновлений, которые человек откатил. Их не предлагаем снова."""
    try:
        return {int(x) for x in open(REJECTED, encoding="utf-8").read().split()}
    except Exception:
        return set()


def add_rejected(n):
    os.makedirs(BACKUP_ROOT, exist_ok=True)
    got = read_rejected() | {int(n)}
    with open(REJECTED, "w", encoding="utf-8") as f:
        f.write("\n".join(str(x) for x in sorted(got)) + "\n")


# ---------------------------------------------------------------- сеть

def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "comfy-pocket"})
    return urllib.request.urlopen(req, timeout=timeout).read()


def what_is_new(current):
    """Список того, что вышло новее установленного. Пусто — значит нечего ставить."""
    try:
        data = json.loads(fetch(INDEX_URL).decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return []          # обновлений ещё не выкладывали — это не поломка
        raise
    items = [p for p in data.get("patches", []) if int(p.get("n", 0)) > current]
    return sorted(items, key=lambda p: int(p["n"]))


# ---------------------------------------------------------------- проверки

def safe_members(zf):
    """
    Отбираем из архива только то, что можно класть.

    Архив приходит из интернета, поэтому имена внутри него проверяем: путь
    с ".." или с буквой диска положил бы файл куда угодно на компьютере.
    Такие записи выбрасываем молча — их там быть не должно.
    """
    out = []
    for info in zf.infolist():
        if info.is_dir():
            continue
        name = info.filename.replace("\\", "/").lstrip("/")
        if not name or ".." in name.split("/") or ":" in name:
            line(f"  пропускаю подозрительное имя: {info.filename}")
            continue
        if any(name == p or name.startswith(p + "/") for p in NEVER_TOUCH):
            line(f"  пропускаю (эту папку не трогаем): {name}")
            continue
        if name == NOTE_NAME:
            continue          # это рассказ для человека, а не файл сборки
        out.append((info, name))
    return out


def sha256(b):
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------- установка

def apply_patch(p):
    """Ставит один патч. Возвращает True, если получилось."""
    n = int(p["n"])
    title = p.get("title", "")
    line(f"\n--- обновление {n}: {title} ---")

    line("  качаю...")
    blob = fetch(BASE_URL + p["file"], timeout=180)
    line("  скачано " + (f"{len(blob)//1024} КБ" if len(blob) >= 1024
                         else f"{len(blob)} байт"))

    want = p.get("sha256")
    if want:
        got = sha256(blob)
        if got != want:
            line("  ОШИБКА: файл скачался повреждённым, ставить не буду.")
            line("  Попробуй запустить ещё раз — скорее всего оборвалась связь.")
            return False

    tmp = os.path.join(HERE, f"_обновление_{n}.zip")
    with open(tmp, "wb") as f:
        f.write(blob)

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = os.path.join(BACKUP_ROOT, f"до_обновления_{n:03d}_{stamp}")
    replaced, added = [], []

    try:
        with zipfile.ZipFile(tmp) as zf:
            members = safe_members(zf)

            # Сначала откладываем всё, что будет затёрто. Если на середине
            # что-то пойдёт не так, откат уже возможен.
            for info, name in members:
                dst = os.path.join(HERE, name.replace("/", os.sep))
                if os.path.exists(dst):
                    keep = os.path.join(backup, name.replace("/", os.sep))
                    os.makedirs(os.path.dirname(keep), exist_ok=True)
                    shutil.copy2(dst, keep)
                    replaced.append(name)
                else:
                    added.append(name)

            # Теперь кладём новое. Всё, что лежит в патче, ставится:
            # что класть, решает тот, кто патч собрал.
            for info, name in members:
                dst = os.path.join(HERE, name.replace("/", os.sep))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(dst, "wb") as f:
                    f.write(zf.read(info))

            # Рассказ автора патча, если он есть.
            if NOTE_NAME in zf.namelist():
                line("")
                for ln in zf.read(NOTE_NAME).decode("utf-8", "replace").splitlines():
                    line("  " + ln)
    finally:
        try:
            os.remove(tmp)
        except Exception:
            pass

    if replaced or added:
        os.makedirs(backup, exist_ok=True)
        with open(os.path.join(backup, "что_было.json"), "w", encoding="utf-8") as f:
            json.dump({"обновление": n, "версия_до": n - 1,
                       "заменено": replaced, "добавлено": added},
                      f, ensure_ascii=False, indent=2)

    line(f"\n  заменено файлов: {len(replaced)}, добавлено новых: {len(added)}")
    if replaced or added:
        line(f"  старое отложено сюда: бэкап\\{os.path.basename(backup)}")
    return True


def update():
    """Проверяет и ставит всё, что вышло. Возвращает установленную версию."""
    current = read_version()
    line(f"Установлена версия: {current}")
    line("Смотрю, что нового вышло...")

    try:
        items = what_is_new(current)
    except Exception as e:
        line(f"Не получилось проверить обновления: {e}")
        line("Работаем на том, что стоит. Это не поломка — бывает, что нет связи.")
        return current

    # Обновления идут по порядку и опираются друг на друга. Если человек
    # что-то откатил, дальше этого места не идём: следующее обновление
    # рассчитано на изменения из откаченного и легло бы криво.
    skip = read_rejected()
    for i, p in enumerate(items):
        if int(p["n"]) in skip:
            line(f"Обновление {p['n']} ты откатывал — дальше не иду.")
            if items[i + 1:]:
                line(f"Из-за этого жду и следующие: "
                     f"{', '.join(str(x['n']) for x in items[i + 1:])}. "
                     f"Они рассчитаны на то, что {p['n']} стоит.")
            line("Передумал — сотри файл  бэкап\\не_ставить.txt  и запусти снова.")
            items = items[:i]
            break

    if not items:
        line("Новых обновлений нет.\n")
        return current

    line(f"Есть новое: {len(items)} шт.")
    for p in items:
        if not apply_patch(p):
            line("\nОстановился на этом обновлении. Что успело поставиться — осталось.")
            break
        current = int(p["n"])
        write_version(current)

    line(f"\nТеперь установлена версия: {current}\n")
    return current


# ---------------------------------------------------------------- откат

def rollback():
    """Возвращает то, что было до последнего обновления."""
    if not os.path.isdir(BACKUP_ROOT):
        line("Откатывать нечего — обновления ещё не ставились.")
        return

    folders = sorted(d for d in os.listdir(BACKUP_ROOT)
                     if os.path.isdir(os.path.join(BACKUP_ROOT, d)))
    if not folders:
        line("Откатывать нечего — отложенного не нашлось.")
        return

    last = os.path.join(BACKUP_ROOT, folders[-1])
    rec_path = os.path.join(last, "что_было.json")
    if not os.path.exists(rec_path):
        line(f"В папке {folders[-1]} нет записи о том, что менялось. Не трогаю.")
        return

    rec = json.load(open(rec_path, encoding="utf-8"))
    line(f"Возвращаю всё, как было до обновления {rec['обновление']}.")
    line(f"Отложено было: {folders[-1]}\n")

    for name in rec.get("заменено", []):
        src = os.path.join(last, name.replace("/", os.sep))
        dst = os.path.join(HERE, name.replace("/", os.sep))
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            line(f"  вернул: {name}")

    for name in rec.get("добавлено", []):
        dst = os.path.join(HERE, name.replace("/", os.sep))
        if os.path.exists(dst):
            os.remove(dst)
            line(f"  убрал новый: {name}")

    write_version(int(rec.get("версия_до", 0)))
    add_rejected(rec["обновление"])
    os.rename(last, last + "_ОТКАЧЕНО")

    line(f"\nГотово. Снова стоит версия {read_version()}.")
    line(f"Обновление {rec['обновление']} больше ставиться не будет — записал")
    line(f"его в  бэкап\\не_ставить.txt . Иначе следующий же запуск вернул бы")
    line(f"обратно то, от чего ты только что избавился.")
    line(f"\nПередумаешь — сотри эту строчку из того файла.\n")


# ---------------------------------------------------------------- запуск

def launch():
    if not os.path.exists(PY):
        line("Не нашёл python_embeded\\python.exe — сборка распакована не полностью.")
        return 1

    os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)

    line("Запускаю мост Photoshop отдельным окном (порт 8189)...")
    try:
        subprocess.Popen([PY, "-s", os.path.join(HERE, "ps_bridge.py")],
                         cwd=HERE, creationflags=subprocess.CREATE_NEW_CONSOLE)
    except Exception as e:
        line(f"  мост не поднялся: {e}")
        line("  Рисовать в ComfyUI можно, панель в Photoshop работать не будет.")

    line("Запускаю ComfyUI: http://127.0.0.1:8188 (браузер откроется сам)")
    line("Это окно не закрывай, пока работаешь. Закрыть = остановить.\n")

    log = open(os.path.join(HERE, "logs", "comfyui_server.log"), "a",
               encoding="utf-8", errors="replace", buffering=1)
    proc = subprocess.Popen(
        [PY, "-s", os.path.join(HERE, "ComfyUI", "main.py"),
         "--port", "8188", "--auto-launch"],
        cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace", bufsize=1)

    try:
        for ln in proc.stdout:
            sys.stdout.write(ln)
            sys.stdout.flush()
            log.write(ln)
    except KeyboardInterrupt:
        proc.terminate()
    finally:
        log.close()
    return proc.wait()


# ---------------------------------------------------------------- главное

if __name__ == "__main__":
    args = [a.lower() for a in sys.argv[1:]]

    if "--откат" in args or "--rollback" in args:
        rollback()
        input("Нажми Enter, чтобы закрыть окно.")
        sys.exit(0)

    line("=" * 60)
    line("  comfy-pocket")
    line("=" * 60)

    if "--без-обновлений" not in args:
        update()
    else:
        line(f"Установлена версия: {read_version()} (проверку обновлений пропустил)\n")

    code = launch()
    if code:
        line(f"\nComfyUI закрылся с кодом {code}.")
        line("Если это неожиданно — нажми СОБРАТЬ_ЛОГИ.bat и пришли архив.")
        input("Нажми Enter, чтобы закрыть окно.")
    sys.exit(code)
