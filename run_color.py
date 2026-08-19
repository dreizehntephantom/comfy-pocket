# Рендер ПО ЦВЕТОВОЙ КОМПОЗИЦИИ С КАРТИНКИ (T2I-Adapter), парити с tensor.art.
# Настройки -> config.txt | Промпт -> prompt.txt | Негатив -> negative.txt
#
# КАК ПОЛЬЗОВАТЬСЯ:
#   1. Кинь картинку с нужной раскладкой цвета в  color\donor\  (имя любое)
#   2. Запусти  РЕНДЕР_ЦВЕТ.bat
#   Цветовая сетка ляжет в  color\map.png  и будет перезаписываться каждый раз.
#
# ЧТО ЭТО ВООБЩЕ ДЕЛАЕТ
#   Донора размазывает в крупную цветную мозаику: рисунка не остаётся вовсе,
#   остаётся только "тут светлое пятно, тут тёмный угол, тут зелёное". Дальше
#   модель расставляет цвета по тем же местам.
#   Форму и линии она НЕ держит — для этого есть РЕНДЕР_ПОЗА и РЕНДЕР_КОНТУР.
#
# Запуск из консоли:  python_embeded\python.exe run_color.py [картинка] [СИД]
#   картинка — необязательна, по умолчанию берётся свежая из color\donor\
#   [СИД]    — необязательный. Без него случайный. При count>1 инкрементится.
#
# Сила: config.txt -> color_strength (0.6 = как на tensor.art).
# Крупность мозаики: config.txt -> color_resolution (512 = 8 клеток по короткой
#   стороне, как на tensor.art; 1024 = 16 клеток, композиция держится точнее).
#
# Картинки -> ComfyUI\output\ГГГГ-ММ-ДД\ . Цветовая сетка -> color\map.png.
import json, time, urllib.request, os, sys, random, datetime, shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _log; _log.start()
HOST = "http://127.0.0.1:8188"
HERE = os.path.dirname(os.path.abspath(__file__))
OUTROOT = os.path.join(HERE, "ComfyUI", "output")
INPUTDIR = os.path.join(HERE, "ComfyUI", "input")

# Рабочая папка цвета: сюда кладёшь донора, сюда же ложится цветовая сетка
COLORDIR = os.path.join(HERE, "color")
DONORDIR = os.path.join(COLORDIR, "donor")
MAPFILE = os.path.join(COLORDIR, "map.png")
IMG_EXT = (".png", ".jpg", ".jpeg", ".webp", ".bmp")

def find_donor():
    """Самая свежая картинка в color\\donor\\ . Имя задавать не нужно."""
    if not os.path.isdir(DONORDIR):
        return None
    files = [os.path.join(DONORDIR, f) for f in os.listdir(DONORDIR)
             if f.lower().endswith(IMG_EXT)]
    if not files:
        return None
    files.sort(key=os.path.getmtime, reverse=True)
    if len(files) > 1:
        print(f"В color\\donor\\ несколько картинок ({len(files)}), беру самую свежую: "
              f"{os.path.basename(files[0])}")
    return files[0]

def rd(name):
    p = os.path.join(HERE, name)
    return open(p, encoding="utf-8").read().strip() if os.path.exists(p) else None

def load_config():
    cfg = {}
    p = os.path.join(HERE, "config.txt")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            cfg[k.strip().lower()] = v.strip()
    return cfg

def post(path, obj):
    req = urllib.request.Request(HOST + path, data=json.dumps(obj).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=60))

def get(path):
    return json.load(urllib.request.urlopen(HOST + path, timeout=120))

# --- настройки ---
c = load_config()
model = c.get("model", "anillustriousXL_v14")
if not model.endswith(".safetensors"):
    model += ".safetensors"
lora = c.get("lora", "sasaminanime")
lora_w = c.get("lora_weight", "0.8")
steps = int(c.get("steps", "25"))
cfg_scale = float(c.get("cfg", "5"))
width = int(c.get("width", "1536"))
height = int(c.get("height", "1536"))
count = max(1, int(c.get("count", "1")))
# сила цвета: свой ключ, но если не задан — падаем на depth_strength, чтобы не дублировать
strength = float(c.get("color_strength", c.get("depth_strength", "0.6")))
grid_res = int(c.get("color_resolution", "512"))
# по какому куску имени искать модель. t2i = адаптер, как на tensor.art
want_cn = c.get("color_model", "t2i").lower()

pos = rd("prompt.txt") or ""
neg = rd("negative.txt") or ""

# --- аргументы: картинка-донор и сид ---
args = sys.argv[1:]
donor_arg = None
base_seed = None
for a in args:
    if a.lstrip("-").isdigit():
        base_seed = int(a)
    else:
        donor_arg = a
# Приоритет: аргумент -> config.txt -> папка color\donor\
donor_arg = donor_arg or c.get("color_image") or find_donor()

if not donor_arg:
    os.makedirs(DONORDIR, exist_ok=True)
    sys.exit(f"Не нашёл картинку с нужной раскладкой цвета.\n"
             f"Положи любую картинку сюда и запусти снова:\n  {DONORDIR}\n"
             f"(папку я уже создал)")
if not os.path.exists(donor_arg):
    sys.exit(f"Не нашёл картинку-донор: {donor_arg}")

# ComfyUI грузит картинки только из своей папки input — копируем туда
os.makedirs(INPUTDIR, exist_ok=True)
donor_name = "color_donor" + os.path.splitext(donor_arg)[1].lower()
shutil.copy2(donor_arg, os.path.join(INPUTDIR, donor_name))

# --- холст под пропорции донора ---
# Если холст и донор разной ориентации, цветовую сетку растягивает и композиция едет.
# По умолчанию берём пропорции донора, сохраняя количество пикселей из config.txt.
# Отключить:  config.txt -> color_fit = config
if c.get("color_fit", c.get("depth_fit", "donor")).lower() != "config":
    try:
        from PIL import Image
        with Image.open(donor_arg) as im:
            dw, dh = im.size
        budget = width * height
        ratio = dw / dh
        nw = int(round((budget * ratio) ** 0.5 / 64)) * 64
        nh = int(round((budget / ratio) ** 0.5 / 64)) * 64
        if (nw, nh) != (width, height):
            print(f"Холст подогнан под донора ({dw}x{dh}): {width}x{height} -> {nw}x{nh}")
            width, height = max(nw, 64), max(nh, 64)
    except Exception as e:
        print("не смог прочитать размер донора, беру из config.txt:", e)

today = datetime.datetime.now().strftime("%Y-%m-%d")

# --- модель: ищем адаптер по куску имени из color_model ---
# Отдельного ЦВЕТОВОГО адаптера под SDXL не существует — его выпустили только
# под старую SD 1.5. На tensor.art цветовую сетку скармливают КОНТУРНОМУ
# адаптеру t2i-adapter_xl_canny, и мы делаем один в один так же.
names = get("/object_info/ControlNetLoader")["ControlNetLoader"]["input"]["required"]["control_net_name"][0]
cn_name = next((n for n in names if want_cn in n.lower()), None)
if not cn_name:
    sys.exit(
        f"Не нашёл модель, в имени которой есть '{want_cn}'.\n"
        f"Сейчас в ComfyUI\\models\\controlnet\\ есть:\n  "
        + "\n  ".join(names or ["(пусто)"]) + "\n\n"
        "Для полного совпадения с tensor.art нужен файл\n"
        "  t2i-adapter_xl_canny.safetensors\n"
        "https://huggingface.co/xingren23/comfyflow-models/tree/main/controlnet\n"
        "Положить в  ComfyUI\\models\\controlnet\\  (можно прямо туда, без подпапки).\n\n"
        "Либо, чтобы попробовать на том, что уже лежит, впиши в config.txt:\n"
        "  color_model = canny\n"
        "Это возьмёт наш большой xinsir. Он не советует, а командует, и в мозаике\n"
        "будет видеть края клеток — результат другой, но посмотреть стоит.")

def build(seed):
    return {
      "10002": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": model}},
      "10031": {"class_type": "LoraTagLoader", "inputs": {"text": f"<lora:{lora}:{lora_w}>",
                "model": ["10002", 0], "clip": ["10002", 1]}},
      "10032": {"class_type": "VAELoader", "inputs": {"vae_name": "sdxl-vae-fp16-fix.safetensors"}},
      "10033": {"class_type": "CLIPSetLastLayer", "inputs": {"stop_at_clip_layer": -2, "clip": ["10031", 1]}},
      "10051": {"class_type": "BNK_CLIPTextEncodeAdvanced", "inputs": {"text": pos, "clip": ["10033", 0],
                "token_normalization": "none", "weight_interpretation": "comfy"}},
      "10052": {"class_type": "BNK_CLIPTextEncodeAdvanced", "inputs": {"text": neg, "clip": ["10033", 0],
                "token_normalization": "none", "weight_interpretation": "comfy"}},
      "10088": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
      "10109": {"class_type": "LoadImage", "inputs": {"image": donor_name}},
      "10117": {"class_type": "ColorPreprocessor",
                "inputs": {"resolution": grid_res, "image": ["10109", 0]}},
      "10124": {"class_type": "ControlNetLoader", "inputs": {"control_net_name": cn_name}},
      "10125": {"class_type": "ControlNetApplyAdvanced",
                "inputs": {"strength": strength, "start_percent": 0.0, "end_percent": 1.0,
                           "control_net": ["10124", 0], "image": ["10117", 0],
                           "positive": ["10051", 0], "negative": ["10052", 0]}},
      "11002": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": steps, "cfg": cfg_scale,
                "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": 1.0,
                "model": ["10031", 0], "positive": ["10125", 0], "negative": ["10125", 1],
                "latent_image": ["10088", 0]}},
      "11029": {"class_type": "VAEDecode", "inputs": {"samples": ["11002", 0], "vae": ["10032", 0]}},
      "12006": {"class_type": "SaveImage", "inputs": {"filename_prefix": today + "/color", "images": ["11029", 0]}},
      "12007": {"class_type": "SaveImage", "inputs": {"filename_prefix": today + "/colormap", "images": ["10117", 0]}},
    }

print(f"Цвет с: {donor_arg}")
print(f"Модель={model} | Лора={lora}:{lora_w} | steps={steps} cfg={cfg_scale} {width}x{height} "
      f"| сила цвета={strength} | мозаика={grid_res} ({grid_res // 64} клеток) "
      f"| адаптер={cn_name} | картинок={count}")

folders = []
for i in range(count):
    seed = (base_seed + i) if base_seed is not None else random.randint(0, 2**32 - 1)
    print(f"[{i+1}/{count}] seed={seed} ...", flush=True)
    r = post("/prompt", {"prompt": build(seed), "client_id": "claudecolor"})
    pid = r.get("prompt_id")
    if not pid:
        print("  ОШИБКА постановки:", json.dumps(r, ensure_ascii=False)[:2000]); continue
    t0 = time.time()
    h = {}
    while True:
        h = get(f"/history/{pid}")
        if pid in h:
            break
        if time.time() - t0 > 600:
            print("  таймаут"); break
        time.sleep(2)
    entry = h.get(pid, {}); status = entry.get("status", {})
    for _, out in entry.get("outputs", {}).items():
        for img in out.get("images", []):
            full = os.path.join(OUTROOT, img.get("subfolder", ""), img.get("filename"))
            # цветовая сетка не копится в output — она одна и перезаписывается
            if os.path.basename(full).startswith("colormap"):
                # При count>1 препроцессор кешируется: ComfyUI отдаёт то же имя,
                # а файла уже нет — сетку забрали на первой картинке. Это не ошибка.
                if not os.path.exists(full):
                    continue
                try:
                    os.makedirs(COLORDIR, exist_ok=True)
                    shutil.copy2(full, MAPFILE)
                    os.remove(full)
                    print("  цветовая сетка:", MAPFILE, flush=True)
                except Exception as e:
                    print("  сетку не перенёс:", e)
                continue
            print("  готово:", full, flush=True)
            folders.append(os.path.dirname(full))
    if status.get("status_str") == "error":
        for m in status.get("messages", []):
            if m[0] == "execution_error":
                print("  ОШИБКА:", m[1].get("node_type"), "->", m[1].get("exception_message"))

print(f"=== ВСЁ ГОТОВО: {len(folders)} файлов ===")
for f in dict.fromkeys(folders):
    try:
        os.startfile(f)
    except Exception as e:
        print("не открыл папку:", e)
