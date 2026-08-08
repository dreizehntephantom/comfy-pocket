# Собирает диагностику окружения в logs\diag.txt и пакует всю папку logs\
# в один zip (на рабочий стол, а если его нет — рядом со скриптом).
# Запуск: СОБРАТЬ_ЛОГИ.bat  ->  друг присылает получившийся zip нам.
import os, sys, io, json, time, platform, shutil, datetime, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(HERE, "logs")
os.makedirs(LOGS, exist_ok=True)
out = io.StringIO()


def line(s=""):
    out.write(str(s) + "\n")


def human(n):
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} PB"


line("=" * 64)
line("ДИАГНОСТИКА ПОРТАБЕЛЬНОГО ComfyUI")
line("время: " + datetime.datetime.now().isoformat(timespec="seconds"))
line("папка: " + HERE)
line("=" * 64)

# --- система ---
line("\n[СИСТЕМА]")
line("ОС        : " + platform.platform())
line("процессор : " + (platform.processor() or "?") + f"  (ядер: {os.cpu_count()})")
try:
    import ctypes
    class MS(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    m = MS(); m.dwLength = ctypes.sizeof(MS)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    line(f"ОЗУ       : всего {human(m.ullTotalPhys)}, свободно {human(m.ullAvailPhys)}")
except Exception as e:
    line("ОЗУ       : не определил (" + str(e) + ")")
try:
    du = shutil.disk_usage(HERE)
    line(f"диск      : свободно {human(du.free)} из {human(du.total)}")
except Exception as e:
    line("диск      : не определил (" + str(e) + ")")
line("python    : " + sys.version.split()[0])

# --- torch / GPU ---
line("\n[TORCH / ВИДЕОКАРТА]")
try:
    import torch
    line("torch        : " + torch.__version__)
    line("cuda сборка  : " + str(torch.version.cuda))
    avail = torch.cuda.is_available()
    line("cuda доступна: " + ("ДА" if avail else "НЕТ (пойдёт на CPU, медленно)"))
    if avail:
        for i in range(torch.cuda.device_count()):
            p = torch.cuda.get_device_properties(i)
            line(f"  GPU {i}: {p.name}  VRAM {human(p.total_memory)}")
except Exception as e:
    line("torch не импортировался: " + str(e))

# --- ComfyUI жив? ---
line("\n[COMFYUI на 127.0.0.1:8188]")
try:
    with urllib.request.urlopen("http://127.0.0.1:8188/system_stats", timeout=5) as r:
        st = json.load(r)
    line("отвечает: ДА")
    dev = (st.get("devices") or [{}])[0]
    if dev:
        line(f"  устройство: {dev.get('name')}  тип: {dev.get('type')}")
        if dev.get("vram_total"):
            line(f"  VRAM: всего {human(dev['vram_total'])}, свободно {human(dev.get('vram_free',0))}")
except Exception as e:
    line("отвечает: НЕТ — сервер не запущен или упал (" + str(e) + ")")
    line("  -> сначала запусти ЗАПУСК_ComfyUI.bat, потом жми СОБРАТЬ_ЛОГИ")

# --- модели ---
line("\n[МОДЕЛИ в ComfyUI\\models]")
mroot = os.path.join(HERE, "ComfyUI", "models")
if os.path.isdir(mroot):
    for dirpath, _, files in os.walk(mroot):
        for fn in files:
            if fn.lower().endswith((".safetensors", ".bin", ".pth", ".onnx", ".ckpt", ".pt")):
                fp = os.path.join(dirpath, fn)
                rel = os.path.relpath(fp, mroot)
                try:
                    line(f"  {rel}  ({human(os.path.getsize(fp))})")
                except Exception:
                    line(f"  {rel}  (размер?)")
else:
    line("  папка models не найдена!")

# --- конфиги ---
for cfg in ("config.txt", "config_ps.txt", "config_ip.txt", "config_ref.txt"):
    p = os.path.join(HERE, cfg)
    line(f"\n[{cfg}]")
    if os.path.exists(p):
        try:
            line(open(p, encoding="utf-8").read().rstrip())
        except Exception as e:
            line("  не прочитал: " + str(e))
    else:
        line("  (нет файла)")

# --- сохранить diag.txt ---
diag_path = os.path.join(LOGS, "diag.txt")
with open(diag_path, "w", encoding="utf-8") as f:
    f.write(out.getvalue())
print(out.getvalue())
print("=" * 64)
print("diag.txt записан:", diag_path)

# --- упаковать logs\ в zip ---
ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
base_name = "ComfyUI_logs_" + ts
desktop = os.path.join(os.path.expanduser("~"), "Desktop")
target_dir = desktop if os.path.isdir(desktop) else HERE
try:
    zip_path = shutil.make_archive(os.path.join(target_dir, base_name), "zip", LOGS)
    print("\nГОТОВО. Архив с логами:")
    print("   " + zip_path)
    print("\n>>> Пришли этот ZIP-файл нам — по нему мы поймём, что починить. <<<")
except Exception as e:
    print("Не смог упаковать zip:", e)
    print("Тогда пришли вручную всю папку:", LOGS)
