# Рендер через ComfyUI (синхро с tensor.art).
# Настройки -> config.txt | Промпт -> prompt.txt | Негатив -> negative.txt
# Сид: первым аргументом (python run_workflow.py 2645234451). Без него — случайный.
#   При count>1 сид инкрементится (seed, seed+1, ...); если сид не задан — каждый случайный.
# Картинки -> ComfyUI\output\ГГГГ-ММ-ДД\ . Папка открывается, КОГДА ГОТОВЫ ВСЕ.
import json, time, urllib.request, os, sys, random, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _log; _log.start()
HOST = "http://127.0.0.1:8188"
HERE = os.path.dirname(os.path.abspath(__file__))
OUTROOT = os.path.join(HERE, "ComfyUI", "output")

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

def envbool(name, default):
    v = os.environ.get(name)
    return default if v is None else v not in ("0", "false", "False")

# --- настройки ---
c = load_config()
model = c.get("model", "newgroundsMix_v20")
if not model.endswith(".safetensors"):
    model += ".safetensors"
lora = c.get("lora", "LoraComicPcv4")
lora_w = c.get("lora_weight", "0.8")
steps = int(c.get("steps", "25"))
cfg_scale = float(c.get("cfg", "5"))
width = int(c.get("width", "1024"))
height = int(c.get("height", "1536"))
count = max(1, int(c.get("count", "1")))

pos = rd("prompt.txt")
neg = rd("negative.txt")
base_seed = int(sys.argv[1]) if len(sys.argv) > 1 else None
today = datetime.datetime.now().strftime("%Y-%m-%d")

template = json.load(open(os.path.join(HERE, "workflow_api.json"), encoding="utf-8"))
oi = get("/object_info")
opt = oi["smZ Settings"]["input"]["optional"]
OVR = {"RNG": os.environ.get("RNG", "cpu"), "ENSD": 31337, "eta": 1.0, "enable_emphasis": True,
       "Use CFGDenoiser": envbool("CFGD", True), "sgm_noise_multiplier": envbool("SGM", True)}

print(f"Модель={model} | Лора={lora}:{lora_w} | steps={steps} cfg={cfg_scale} {width}x{height} | картинок={count}")
folders = []
for i in range(count):
    seed = (base_seed + i) if base_seed is not None else random.randint(0, 2**32 - 1)
    wf = json.loads(json.dumps(template))  # глубокая копия
    for nid, node in wf.items():
        ct = node["class_type"]
        if ct == "CheckpointLoaderSimple":
            node["inputs"]["ckpt_name"] = model
        elif ct == "LoraTagLoader":
            node["inputs"]["text"] = f"<lora:{lora}:{lora_w}>"
        elif ct == "smZ Settings":
            link = node["inputs"]["*"]
            full = {}
            for key, spec in opt.items():
                meta = spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {}
                full[key] = meta["default"] if "default" in meta else (spec[0][0] if isinstance(spec[0], list) and spec[0] else "")
            full.update(OVR); full["*"] = link
            node["inputs"] = full
        elif ct == "BNK_CLIPTextEncodeAdvanced":
            if nid == "10051" and pos is not None:
                node["inputs"]["text"] = pos
            if nid == "10052" and neg is not None:
                node["inputs"]["text"] = neg
        elif ct == "EmptyLatentImage":
            node["inputs"]["width"] = width
            node["inputs"]["height"] = height
        elif ct == "KSampler":
            node["inputs"]["seed"] = seed
            node["inputs"]["steps"] = steps
            node["inputs"]["cfg"] = cfg_scale
        elif ct == "SaveImage":
            node["inputs"]["filename_prefix"] = today + "/sync"

    print(f"[{i+1}/{count}] seed={seed} ...", flush=True)
    r = post("/prompt", {"prompt": wf, "client_id": "claudesync"})
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

print(f"=== ВСЁ ГОТОВО: {len(folders)} из {count} ===")
# открыть папку ОДИН раз, когда все готовы
for f in dict.fromkeys(folders):
    try:
        os.startfile(f)
    except Exception as e:
        print("не открыл папку:", e)
