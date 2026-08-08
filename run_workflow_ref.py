# Reference-only рендер через ComfyUI: генерит по картинкам-референсам из папки (ref_dir).
# Настройки -> config_ref.txt | Промпт -> prompt.txt | Негатив -> negative.txt
# Для КАЖДОЙ картинки из ref_dir делает count вариаций (seed инкрементится сквозным счётчиком).
# Сид: первым аргументом (python run_workflow_ref.py 2645234451). Без него — случайный.
# Картинки -> ComfyUI\output\ГГГГ-ММ-ДД\refonly... . Папка открывается, КОГДА ГОТОВЫ ВСЕ.
import json, time, urllib.request, os, sys, random, datetime, shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _log; _log.start()
HOST = "http://127.0.0.1:8188"
HERE = os.path.dirname(os.path.abspath(__file__))
OUTROOT = os.path.join(HERE, "ComfyUI", "output")
INPUTDIR = os.path.join(HERE, "ComfyUI", "input")
EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")

def rd(name):
    p = os.path.join(HERE, name)
    return open(p, encoding="utf-8").read().strip() if os.path.exists(p) else None

def load_config():
    cfg = {}
    p = os.path.join(HERE, "config_ref.txt")
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
lora = c.get("lora", "").strip()
lora_w = c.get("lora_weight", "0.9")
lora_tag = f"<lora:{lora}:{lora_w}>" if lora and lora.lower() != "none" else ""
steps = int(c.get("steps", "25"))
cfg_scale = float(c.get("cfg", "4"))
width = int(c.get("width", "1024"))
height = int(c.get("height", "1536"))
count = max(1, int(c.get("count", "1")))
ref_dir = c.get("ref_dir", "").strip().strip('"')
if ref_dir and not os.path.isabs(ref_dir):
    ref_dir = os.path.join(HERE, ref_dir)

pos = rd("prompt.txt")
neg = rd("negative.txt")
base_seed = int(sys.argv[1]) if len(sys.argv) > 1 else None
today = datetime.datetime.now().strftime("%Y-%m-%d")

# --- собрать список референсов ---
if not ref_dir or not os.path.isdir(ref_dir):
    print("ОШИБКА: ref_dir не задан или не папка:", ref_dir)
    sys.exit(1)
refs = [os.path.join(ref_dir, f) for f in sorted(os.listdir(ref_dir))
        if f.lower().endswith(EXTS)]
if not refs:
    print("ОШИБКА: в папке нет картинок:", ref_dir)
    sys.exit(1)

template = json.load(open(os.path.join(HERE, "workflow_api_ref.json"), encoding="utf-8"))

total = len(refs) * count
print(f"Модель={model} | Лора={lora_tag or 'нет'} | steps={steps} cfg={cfg_scale} {width}x{height}")
print(f"Референсов={len(refs)} x вариаций={count} = {total} картинок")

folders = []
gidx = 0
for ref_path in refs:
    base = os.path.basename(ref_path)
    safe = "_ref_" + base
    try:
        shutil.copyfile(ref_path, os.path.join(INPUTDIR, safe))
    except Exception as e:
        print("  не скопировал референс:", base, e); continue
    print(f"--- референс: {base} ---", flush=True)
    for v in range(count):
        seed = (base_seed + gidx) if base_seed is not None else random.randint(0, 2**32 - 1)
        gidx += 1
        wf = json.loads(json.dumps(template))  # глубокая копия
        for nid, node in wf.items():
            ct = node["class_type"]
            if ct == "CheckpointLoaderSimple":
                node["inputs"]["ckpt_name"] = model
            elif ct == "LoraTagLoader":
                node["inputs"]["text"] = lora_tag
            elif ct == "BNK_CLIPTextEncodeAdvanced":
                if nid == "10051" and pos is not None:
                    node["inputs"]["text"] = pos
                if nid == "10052" and neg is not None:
                    node["inputs"]["text"] = neg
            elif ct == "LoadImage":
                node["inputs"]["image"] = safe
            elif ct == "ImageScale":
                node["inputs"]["width"] = width
                node["inputs"]["height"] = height
            elif ct == "KSampler":
                node["inputs"]["seed"] = seed
                node["inputs"]["steps"] = steps
                node["inputs"]["cfg"] = cfg_scale
            elif ct == "SaveImage":
                node["inputs"]["filename_prefix"] = today + "/refonly"

        print(f"[{gidx}/{total}] seed={seed} ...", flush=True)
        r = post("/prompt", {"prompt": wf, "client_id": "clauderef"})
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
                print("  готово:", full, flush=True)
                folders.append(os.path.dirname(full))
        if status.get("status_str") == "error":
            for m in status.get("messages", []):
                if m[0] == "execution_error":
                    print("  ОШИБКА:", m[1].get("node_type"), "->", m[1].get("exception_message"))

print(f"=== ВСЁ ГОТОВО: {len(folders)} из {total} ===")
for f in dict.fromkeys(folders):
    try:
        os.startfile(f)
    except Exception as e:
        print("не открыл папку:", e)
