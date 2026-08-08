# Дублирует весь вывод (stdout+stderr) в консоль И в файл logs\<инструмент>_<время>.log.
# Смысл: если что-то пойдёт не так, трейсбек сохранится в файл, даже если окно
# моргнуло и закрылось. Друг потом жмёт СОБРАТЬ_ЛОГИ.bat и присылает нам архив.
#
# Подключение — одной строкой сразу после импортов в скрипте:
#     import _log; _log.start()          # имя инструмента возьмётся из имени файла
#     import _log; _log.start("canny")   # или задать явно
import os, sys, datetime, platform, traceback

_started = False


class _Tee:
    # Пишет сразу в несколько потоков (реальную консоль + файл лога).
    def __init__(self, *streams):
        self.streams = [s for s in streams if s is not None]

    def write(self, s):
        for st in self.streams:
            try:
                st.write(s)
                st.flush()
            except Exception:
                pass

    def flush(self):
        for st in self.streams:
            try:
                st.flush()
            except Exception:
                pass


def start(tool=None):
    global _started
    if _started:
        return
    _started = True

    here = os.path.dirname(os.path.abspath(__file__))
    logs = os.path.join(here, "logs")
    try:
        os.makedirs(logs, exist_ok=True)
    except Exception:
        return  # не смогли создать папку логов — молча работаем как раньше

    if not tool:
        tool = os.path.splitext(os.path.basename(sys.argv[0] or "tool"))[0] or "tool"
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(logs, f"{tool}_{ts}.log")

    try:
        f = open(path, "a", encoding="utf-8", buffering=1)
    except Exception:
        return

    f.write("=" * 60 + "\n")
    f.write(f"инструмент : {tool}\n")
    f.write(f"время      : {datetime.datetime.now().isoformat(timespec='seconds')}\n")
    f.write(f"python     : {sys.version.split()[0]}\n")
    f.write(f"ОС         : {platform.platform()}\n")
    f.write(f"аргументы  : {' '.join(sys.argv[1:]) or '(нет)'}\n")
    f.write("=" * 60 + "\n")
    f.flush()

    # Не импортируем torch тут: эти скрипты — HTTP-клиенты, torch им не нужен,
    # а его загрузка тормозила бы каждый запуск. GPU/CUDA-диагностику собирает
    # отдельно _diag.py (СОБРАТЬ_ЛОГИ.bat).

    sys.stdout = _Tee(sys.__stdout__, f)
    sys.stderr = _Tee(sys.__stderr__, f)

    def hook(et, ev, tb):
        try:
            f.write("\n!!! НЕОТЛОВЛЕННАЯ ОШИБКА:\n")
            traceback.print_exception(et, ev, tb, file=f)
            f.flush()
        except Exception:
            pass
        sys.__excepthook__(et, ev, tb)

    sys.excepthook = hook
