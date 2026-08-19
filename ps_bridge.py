# Мост между панелью Photoshop и ComfyUI.
# Панель шлёт: картинку (весь холст), маску-контур, bbox выделения и параметры.
# Мост: заливает их в ComfyUI, гоняет inpaint_onlymasked_api.json, возвращает
# PNG-вырезку по контуру с прозрачностью вокруг + позицию на холсте.
#
# Запуск: python_embeded\python.exe ps_bridge.py   (или МОСТ_PS.bat)
# Настройки модели/лоры/шагов -> config_ps.txt
import json, time, os, io, re, sys, math, uuid, random, base64, urllib.request, urllib.parse, traceback, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from PIL import Image
import numpy as np
from scipy.ndimage import grey_dilation, gaussian_filter, distance_transform_edt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _log; _log.start("ps_bridge")
COMFY = "http://127.0.0.1:8188"
PORT = 8189
CLIENT_ID = "psbridge"

# Прогресс ComfyUI прилетает по вебсокету тому клиенту, чьим client_id поставлена
# задача. Слушаем в фоне и держим последнее состояние для панели.
STATE = {"value": 0, "max": 0, "node": None}
HERE = os.path.dirname(os.path.abspath(__file__))
GRAPH = os.path.join(HERE, "inpaint_onlymasked_api.json")


def load_config():
    cfg = {}
    p = os.path.join(HERE, "config_ps.txt")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            cfg[k.strip().lower()] = v.strip()
    return cfg


def rd(name):
    p = os.path.join(HERE, name)
    return open(p, encoding="utf-8").read().strip() if os.path.exists(p) else ""


def comfy_post(path, obj):
    req = urllib.request.Request(COMFY + path, data=json.dumps(obj).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=60))


def comfy_get(path):
    return json.load(urllib.request.urlopen(COMFY + path, timeout=120))


def comfy_post_raw(path, obj=None):
    # /interrupt отвечает пустым телом — разбирать его как JSON нельзя
    req = urllib.request.Request(COMFY + path, data=json.dumps(obj or {}).encode(),
                                 headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=30).read()


def comfy_view(img):
    # Забираем картинку у самого ComfyUI, а не с диска: где у него папка вывода
    # и на каком она диске — не наше дело.
    q = urllib.parse.urlencode({
        "filename": img["filename"],
        "subfolder": img.get("subfolder", ""),
        "type": img.get("type", "output"),
    })
    return urllib.request.urlopen(f"{COMFY}/view?{q}", timeout=120).read()


def comfy_upload(png_bytes, name):
    boundary = "----b" + uuid.uuid4().hex
    body = io.BytesIO()
    def w(s):
        body.write(s.encode() if isinstance(s, str) else s)
    w(f"--{boundary}\r\n")
    w(f'Content-Disposition: form-data; name="image"; filename="{name}"\r\n')
    w("Content-Type: image/png\r\n\r\n")
    w(png_bytes); w("\r\n")
    w(f"--{boundary}\r\n")
    w('Content-Disposition: form-data; name="overwrite"\r\n\r\ntrue\r\n')
    w(f"--{boundary}--\r\n")
    req = urllib.request.Request(COMFY + "/upload/image", data=body.getvalue(),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    return json.load(urllib.request.urlopen(req, timeout=120))["name"]


def to_png(im):
    b = io.BytesIO(); im.save(b, "PNG"); return b.getvalue()


def to_image(spec, want):
    # Панель шлёт либо base64 PNG, либо сырые пиксели из Photoshop:
    # {"data": b64, "width": w, "height": h, "components": 1|3|4,
    #  "left": x, "top": y, "canvas_width": W, "canvas_height": H}
    # Photoshop отдаёт выделение ЛОСКУТОМ по границам выделения, а не во весь
    # холст — поэтому лоскут вклеиваем на его место в полное полотно.
    if not isinstance(spec, dict):
        return Image.open(io.BytesIO(base64.b64decode(spec))).convert(want)

    raw = base64.b64decode(spec["data"])
    w, h, c = int(spec["width"]), int(spec["height"]), int(spec["components"])
    mode = {1: "L", 3: "RGB", 4: "RGBA"}.get(c)
    if not mode:
        raise ValueError(f"Непонятный формат пикселей: {c} компонент")
    need = w * h * c
    if len(raw) != need:
        raise ValueError(f"Пиксели не сходятся: пришло {len(raw)} байт, "
                         f"ждали {need} ({w}x{h}, {c} компонент)")
    im = Image.frombytes(mode, (w, h), raw).convert(want)

    CW, CH = int(spec.get("canvas_width", w)), int(spec.get("canvas_height", h))
    if (w, h) != (CW, CH):
        canvas = Image.new(want, (CW, CH), 0 if want == "L" else (0, 0, 0))
        canvas.paste(im, (int(spec.get("left", 0)), int(spec.get("top", 0))))
        im = canvas
    return im


def ws_listen():
    # Отдельный поток: слушает прогресс ComfyUI и складывает в STATE.
    # Обрыв связи не смертелен — ComfyUI могли перезапустить, ждём и пробуем снова.
    import websocket
    while True:
        try:
            ws = websocket.create_connection(f"ws://127.0.0.1:8188/ws?clientId={CLIENT_ID}")
            print("  прогресс ComfyUI слушаю", flush=True)
            while True:
                m = ws.recv()
                if not isinstance(m, str):
                    continue
                d = json.loads(m)
                t = d.get("type")
                if t == "progress":
                    STATE["value"] = d["data"].get("value", 0)
                    STATE["max"] = d["data"].get("max", 0)
                elif t == "executing":
                    STATE["node"] = d["data"].get("node")
                elif t in ("execution_success", "execution_error", "execution_interrupted"):
                    STATE["value"] = STATE["max"] = 0
                    STATE["node"] = None
        except Exception:
            STATE["value"] = STATE["max"] = 0
            time.sleep(2)


# Без этих нод граф не соберётся. ComfyUI на неизвестную ноду отвечает {}.
REQUIRED_NODES = {
    "InpaintCropImproved": "ComfyUI-Inpaint-CropAndStitch",
    "InpaintStitchImproved": "ComfyUI-Inpaint-CropAndStitch",
    "LoraTagLoader": "comfyui_lora_tag_loader",
}


def missing_nodes():
    missing = set()
    for node, pack in REQUIRED_NODES.items():
        try:
            if not comfy_get(f"/object_info/{node}"):
                missing.add(pack)
        except Exception:
            return []          # ComfyUI молчит — это другая беда, не наша
    return sorted(missing)


def resolve_model(name):
    # Имя модели с чужой машины (или из чужого конфига) может не существовать.
    # Лучше внятно сказать, что есть, чем упасть внутри ComfyUI.
    try:
        oi = comfy_get("/object_info/CheckpointLoaderSimple")
        avail = oi["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]
    except Exception:
        avail = []
    if not avail:
        raise RuntimeError("ComfyUI не видит ни одной модели — проверь папку checkpoints")
    name = (name or "").strip()
    if not name:
        return avail[0]        # не выбрано ничего — берём первую попавшуюся
    if not name.lower().endswith(".safetensors"):
        name += ".safetensors"
    for a in avail:
        if a.lower() == name.lower():
            return a
    raise RuntimeError(f"Модель '{name}' не найдена. Есть: " + ", ".join(avail[:6]))


def resolve_controlnet(kind, need_sdxl=True):
    # Имя файла не хардкодим: у соседа он может лежать под другим именем.
    # Ищем по словам, как это делают РЕНДЕР_ПОЗА и РЕНДЕР_КОНТУР.
    # need_sdxl=False — для цветового адаптера: он называется t2i-adapter_xl_...,
    # слова "sdxl" в имени нет.
    try:
        oi = comfy_get("/object_info/ControlNetLoader")
        avail = oi["ControlNetLoader"]["input"]["required"]["control_net_name"][0]
    except Exception:
        avail = []
    hit = next((n for n in avail if kind in n.lower()
                and (not need_sdxl or "sdxl" in n.lower())), None)
    if hit:
        return hit
    raise RuntimeError(
        f"Не нашёл модель ControlNet со словом '{kind}' в имени. Она кладётся в "
        f"ComfyUI\\models\\controlnet\\ — что именно, написано там в ЧТО_ЗДЕСЬ.txt. "
        + ("Сейчас там: " + ", ".join(avail) if avail else "Сейчас там пусто."))


def lora_tag(name, weight):
    # LoraTagLoader ждёт имя без расширения, как в prompt.txt у Forge
    if not name:
        return ""
    base = re.sub(r"\.(safetensors|ckpt|pt)$", "", name, flags=re.I)
    return f"<lora:{base}:{weight}>"


def get_lists():
    # Списки берём у самого ComfyUI: он знает про extra_model_paths.yaml и не
    # покажет .json/.png, которых в папке лор половина.
    loras, embs, models = [], [], []
    try:
        oi = comfy_get("/object_info/LoraLoader")
        loras = oi["LoraLoader"]["input"]["required"]["lora_name"][0]
    except Exception as e:
        print("  не забрал список лор:", e, flush=True)
    try:
        embs = comfy_get("/embeddings")
    except Exception as e:
        print("  не забрал список эмбеддингов:", e, flush=True)
    try:
        oi = comfy_get("/object_info/CheckpointLoaderSimple")
        models = oi["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]
    except Exception as e:
        print("  не забрал список моделей:", e, flush=True)
    vaes = []
    try:
        oi = comfy_get("/object_info/VAELoader")
        vaes = oi["VAELoader"]["input"]["required"]["vae_name"][0]
    except Exception as e:
        print("  не забрал список VAE:", e, flush=True)
    # Есть ли чем держать форму. Пусто = панель просто не предложит этот пункт,
    # вместо того чтобы дать нажать и упасть на генерации.
    # Нужны обе половины: узел, который РИСУЕТ карту глубины (из
    # comfyui_controlnet_aux), и модель, которая по ней держит форму.
    cfg = load_config()
    depth_cn = ""
    try:
        if not comfy_get("/object_info/MiDaS-DepthMapPreprocessor"):
            raise RuntimeError("нет узла MiDaS-DepthMapPreprocessor "
                               "(папка custom_nodes\\comfyui_controlnet_aux)")
        depth_cn = resolve_controlnet("depth")
    except Exception as e:
        print("  контроль по объёму недоступен:", e, flush=True)
    color_cn = ""
    try:
        if not comfy_get("/object_info/ColorPreprocessor"):
            raise RuntimeError("нет узла ColorPreprocessor "
                               "(папка custom_nodes\\comfyui_controlnet_aux)")
        color_cn = resolve_controlnet(cfg.get("color_model", "t2i"), need_sdxl=False)
    except Exception as e:
        print("  контроль по цвету недоступен:", e, flush=True)
    return {
        "loras": loras,
        "embeddings": embs,
        "models": models,
        "vaes": vaes,
        "depth_cn": depth_cn,
        "depth_strength": cfg.get("depth_strength", "0.6"),
        "color_cn": color_cn,
        "color_strength": cfg.get("color_strength", "1.5"),
        "vae": cfg.get("vae", ""),
        "model": cfg.get("model", ""),
        "lora": cfg.get("lora", ""),
        "lora_weight": cfg.get("lora_weight", "0.8"),
        "steps": cfg.get("steps", "25"),
        "cfg": cfg.get("cfg", "5"),
        "negative": rd("negative.txt"),
    }


def blend_alpha(mask, blend, shape="gauss"):
    # Растушёвка ЗА контуром: внутри выделения альфа сплошная, затухание уходит
    # наружу и гаснет через blend пикселей. Внутрь контура не заходим никогда.
    if blend <= 0:
        return mask

    if shape == "linear":
        # Прямая линейка: на расстоянии d от контура альфа = 1 - d/blend.
        # Спад ровный, но с изломами в начале и в конце — их видно глазом.
        inside = np.array(mask, dtype=np.uint8) >= 128
        dist = distance_transform_edt(~inside)
        a = np.clip(1.0 - dist / float(blend), 0.0, 1.0)
        a[inside] = 1.0
    else:
        # Гаусс: расширяем на blend/2, затем размываем с sigma=blend/6
        # (3*sigma = blend/2). Плато доходит ровно до контура, весь спад —
        # снаружи, без изломов. Формулу ноды (expand -> blur) копировать нельзя:
        # она прячет шов и заходит внутрь контура, съедая край выделения.
        a = np.array(mask, dtype=np.float32) / 255.0
        d = max(1, int(round(blend / 2.0)))
        k = 2 * d + 1
        # прямоугольное ядро разделяемо — два прохода вместо одного медленного
        # mode="nearest": у края холста продолжаем крайнее значение, иначе
        # размытие подтянет пустоту извне и выделение у края холста поблёкнет
        a = grey_dilation(a, size=(1, k), mode="nearest")
        a = grey_dilation(a, size=(k, 1), mode="nearest")
        a = gaussian_filter(a, sigma=blend / 6.0, mode="nearest")

    return Image.fromarray((np.clip(a, 0.0, 1.0) * 255).astype(np.uint8), "L")


def context_factor(bbox_w, bbox_h, px):
    # Нода расширяет рамку маски множителем, а не пикселями. Считаем множитель так,
    # чтобы поле было НЕ МЕНЬШЕ px по короткой стороне (по длинной выйдет больше).
    side = max(8, min(bbox_w, bbox_h))
    return round(1.0 + (2.0 * px) / side, 4)


def run_inpaint(p):
    cfg = load_config()
    t0 = time.time()

    def meta(spec):
        return {k: v for k, v in spec.items() if k != "data"} if isinstance(spec, dict) else "PNG"
    print("  маска от Photoshop:", meta(p["mask"]), flush=True)

    img = to_image(p["image"], "RGB")
    mask = to_image(p["mask"], "L")
    W, H = img.size
    if mask.size != (W, H):
        # Растягивать маску нельзя: молча получим кашу вместо ошибки.
        raise ValueError(f"Маска {mask.size} не совпадает с холстом {(W, H)}")

    # bbox выделения: панель присылает свой; если нет — считаем по маске
    bbox = p.get("bbox") or mask.getbbox()
    if not bbox:
        raise ValueError("Пустая маска: в Photoshop ничего не выделено")
    x0, y0, x1, y1 = [int(v) for v in bbox]
    bw, bh = x1 - x0, y1 - y0

    # Куда реально легла маска — видно глазами, если что-то не сходится.
    # Кладём рядом со скриптом: где у ComfyUI папка вывода, мы не знаем.
    mbox = mask.getbbox()
    mask.save(os.path.join(HERE, "_last_mask.png"))
    print(f"  маска на холсте {W}x{H}: белое в {mbox} | выделение из PS: {tuple(bbox)}", flush=True)

    context_px = int(p.get("context_px", 64))
    target = int(p.get("target", 1024))          # 0 = оригинальное разрешение
    blend = int(p.get("mask_blend", cfg.get("mask_blend", 32)))
    shape = p.get("blend_shape", "gauss")
    denoise = float(p.get("denoise", cfg.get("denoise", 0.6)))
    if denoise <= 0:
        raise ValueError(f"denoise={denoise} — модель ничего не нарисует. "
                         f"Нужно от 0.05 до 1.0 (точка, не запятая)")
    steps = int(p.get("steps", cfg.get("steps", 25)))
    cfg_scale = float(p.get("cfg", cfg.get("cfg", 5)))
    seed = int(p["seed"]) if p.get("seed") not in (None, "", -1) else random.randint(0, 2**32 - 1)
    pos = (p.get("prompt") or "").strip() or rd("prompt.txt")
    neg = (p.get("negative") or "").strip() or rd("negative.txt")

    # Эмбеддинг живёт отдельно от текста негатива и приклеивается перед ним
    emb = (p.get("neg_embedding") or "").strip()
    if emb:
        neg = f"embedding:{emb}, {neg}" if neg else f"embedding:{emb}"

    model = resolve_model((p.get("model") or "").strip() or cfg.get("model", ""))
    # пустая строка от панели = "без лоры", это не повод лезть в конфиг
    lora = p["lora"] if "lora" in p else cfg.get("lora", "")
    lora_w = p.get("lora_weight") or cfg.get("lora_weight", "0.8")

    tag = uuid.uuid4().hex[:8]
    name_img = comfy_upload(to_png(img), f"ps_{tag}_image.png")
    name_msk = comfy_upload(to_png(Image.merge("RGB", (mask, mask, mask))), f"ps_{tag}_mask.png")

    wf = json.load(open(GRAPH, encoding="utf-8"))
    wf["1"]["inputs"]["ckpt_name"] = model

    # VAE: пусто = берём из самой модели. Иначе граф требовал бы конкретный файл,
    # которого на чужой машине может не быть, и падал бы на старте.
    vae = p["vae"] if "vae" in p else cfg.get("vae", "")
    vae = (vae or "").strip()
    if vae:
        wf["4"]["inputs"]["vae_name"] = vae
    else:
        for nid in ("50", "11"):            # InpaintModelConditioning, VAEDecode
            wf[nid]["inputs"]["vae"] = ["1", 2]   # выход VAE у CheckpointLoaderSimple
        wf.pop("4", None)
    wf["2"]["inputs"]["text"] = lora_tag(lora, lora_w)
    wf["7"]["inputs"]["image"] = name_img
    wf["70"]["inputs"]["image"] = name_msk
    wf["5"]["inputs"]["text"] = pos
    wf["6"]["inputs"]["text"] = neg
    c60 = wf["60"]["inputs"]
    c60["mask_blend_pixels"] = blend
    c60["context_from_mask_extend_factor"] = context_factor(bw, bh, context_px)
    if target > 0:
        c60["output_resize_to_target_size"] = True
        c60["output_target_width"] = target
        c60["output_target_height"] = target
    else:
        c60["output_resize_to_target_size"] = False
    k10 = wf["10"]["inputs"]
    k10["seed"] = seed
    k10["steps"] = steps
    k10["cfg"] = cfg_scale
    k10["denoise"] = denoise

    # Куда сейчас подключено условие. Каждый включённый контроль вклинивается
    # в эту пару и передаёт её дальше, поэтому их можно ставить в любом наборе.
    cond_pos, cond_neg = ["5", 0], ["6", 0]

    # --- держать форму по объёму (ControlNet depth) ---
    # Карту глубины снимаем с ВЫРЕЗАННОГО куска (выход 60->1). Это исходные
    # пиксели до зашумления, то есть модель видит настоящее тело, а не то,
    # что сама рисует. С полного холста брать нельзя: сэмплер работает с
    # вырезкой, размеры не совпадут и карта ляжет мимо.
    # Узлы добавляются, только когда просят: нет контролнета в папке — работает
    # всё остальное, как раньше.
    control = (p.get("control") or "нет").strip().lower()
    csrc = (p.get("control_src") or "canvas").strip().lower()
    cstr = float(p.get("control_strength") or cfg.get("depth_strength", 0.6))
    if control == "depth":
        cn_name = resolve_controlnet("depth")
        # a / bg_threshold / resolution — те же, что в run_depth.py: настройка
        # обкатана, разъезжаться этим двум местам незачем.
        if csrc == "selection":
            # Карта снимается с самой вырезки. Диапазон глубины уходит целиком
            # на выделенный кусок — деталей больше. Но MiDaS видит фрагмент без
            # контекста и может не понять, что перед ним человек.
            wf["80"] = {"class_type": "MiDaS-DepthMapPreprocessor",
                        "inputs": {"a": 6.28, "bg_threshold": 0.1, "resolution": 512,
                                   "image": ["60", 1]}}
            cn_img = ["80", 0]
        else:
            # Карта снимается со всего холста — MiDaS видит фигуру целиком и
            # раскладывает объём правильно. Дальше из готовой карты вырезаем тот
            # же кусок тем же узлом с теми же настройками: рамку он считает по
            # маске и размеру холста, а не по пикселям, поэтому вырезка совпадёт
            # с основной один в один.
            wf["80"] = {"class_type": "MiDaS-DepthMapPreprocessor",
                        "inputs": {"a": 6.28, "bg_threshold": 0.1, "resolution": 512,
                                   "image": ["7", 0]}}
            # Препроцессор отдаёт карту в своём разрешении — возвращаем к размеру
            # холста, иначе второй вырезке не с чем будет совпадать.
            wf["84"] = {"class_type": "ImageScale",
                        "inputs": {"upscale_method": "bilinear", "width": W, "height": H,
                                   "crop": "disabled", "image": ["80", 0]}}
            c85 = dict(c60)
            c85["image"] = ["84", 0]
            wf["85"] = {"class_type": "InpaintCropImproved", "inputs": c85}
            cn_img = ["85", 1]
        wf["81"] = {"class_type": "ControlNetLoader",
                    "inputs": {"control_net_name": cn_name}}
        wf["82"] = {"class_type": "ControlNetApplyAdvanced",
                    "inputs": {"strength": cstr, "start_percent": 0.0, "end_percent": 1.0,
                               "control_net": ["81", 0], "image": cn_img,
                               "positive": cond_pos, "negative": cond_neg}}
        # Показываем ровно то, что ушло в ControlNet, а не промежуточную карту.
        wf["83"] = {"class_type": "PreviewImage", "inputs": {"images": cn_img}}
        cond_pos, cond_neg = ["82", 0], ["82", 1]
        src_txt = "со всего холста" if csrc != "selection" else "с выделения"
        print(f"  форма по объёму: {cn_name} | сила {cstr} | карта {src_txt}", flush=True)

    # --- держать палитру (T2I-Adapter, цветовая сетка) ---
    # Устроено зеркально глубине, но держит другое: не форму, а раскладку цвета
    # и света. Мозаика грубая (8 клеток по короткой стороне), поэтому узор ткани
    # ей не задать — только "здесь тёмно-красное, здесь светлое".
    # Цепляется ПОСЛЕ глубины: включать можно оба сразу, они не спорят.
    color = (p.get("color") or "нет").strip().lower()
    lsrc = (p.get("color_src") or "selection").strip().lower()
    lstr = float(p.get("color_strength") or cfg.get("color_strength", 1.5))
    if color == "color":
        cl_name = resolve_controlnet(cfg.get("color_model", "t2i"), need_sdxl=False)
        if lsrc == "canvas":
            # Палитра всей картинки, вырезанная по месту: новое встанет в цвета
            # сцены и не будет выпадать из общего света.
            wf["90"] = {"class_type": "ColorPreprocessor",
                        "inputs": {"resolution": 512, "image": ["7", 0]}}
            wf["94"] = {"class_type": "ImageScale",
                        "inputs": {"upscale_method": "bilinear", "width": W, "height": H,
                                   "crop": "disabled", "image": ["90", 0]}}
            c95 = dict(c60)
            c95["image"] = ["94", 0]
            wf["95"] = {"class_type": "InpaintCropImproved", "inputs": c95}
            cl_img = ["95", 1]
        else:
            # Палитра самой вырезки. Здесь и живёт главный приём: мазнул в
            # фотошопе нужными цветами прямо по выделению — модель возьмёт
            # ровно их и превратит мазки в настоящую вещь.
            wf["90"] = {"class_type": "ColorPreprocessor",
                        "inputs": {"resolution": 512, "image": ["60", 1]}}
            cl_img = ["90", 0]
        wf["91"] = {"class_type": "ControlNetLoader",
                    "inputs": {"control_net_name": cl_name}}
        wf["92"] = {"class_type": "ControlNetApplyAdvanced",
                    "inputs": {"strength": lstr, "start_percent": 0.0, "end_percent": 1.0,
                               "control_net": ["91", 0], "image": cl_img,
                               "positive": cond_pos, "negative": cond_neg}}
        wf["93"] = {"class_type": "PreviewImage", "inputs": {"images": cl_img}}
        cond_pos, cond_neg = ["92", 0], ["92", 1]
        lsrc_txt = "со всего холста" if lsrc == "canvas" else "с выделения"
        print(f"  палитра: {cl_name} | сила {lstr} | сетка {lsrc_txt}", flush=True)

    wf["50"]["inputs"]["positive"] = cond_pos
    wf["50"]["inputs"]["negative"] = cond_neg

    print(f"  bbox={bw}x{bh} @({x0},{y0}) | контекст {context_px}px -> factor "
          f"{c60['context_from_mask_extend_factor']} | target={target or 'оригинал'} | "
          f"denoise={denoise} | растушёвка {blend}px {shape} | seed={seed}", flush=True)
    print(f"  модель: {model} | VAE: {vae or 'из модели'}", flush=True)
    print(f"  лора: {wf['2']['inputs']['text'] or 'нет'} | негатив: {neg[:60]}...", flush=True)

    r = comfy_post("/prompt", {"prompt": wf, "client_id": CLIENT_ID})
    pid = r.get("prompt_id")
    if not pid:
        raise RuntimeError("ComfyUI не принял задачу: " + json.dumps(r, ensure_ascii=False)[:500])

    while True:
        h = comfy_get(f"/history/{pid}")
        if pid in h:
            break
        if time.time() - t0 > 600:
            raise RuntimeError("Таймаут: ComfyUI не ответил за 10 минут")
        time.sleep(1)

    entry = h[pid]
    status = entry.get("status", {})
    # отмена — это не поломка, панель должна отличать одно от другого
    for m in status.get("messages", []):
        if m[0] == "execution_interrupted":
            raise RuntimeError("прервано")
    if status.get("status_str") == "error":
        for m in status.get("messages", []):
            if m[0] == "execution_error":
                raise RuntimeError(f"{m[1].get('node_type')}: {m[1].get('exception_message')}")
        raise RuntimeError("Ошибка выполнения в ComfyUI")

    # Результат берём у конкретного узла (12 = SaveImage), а не «последний
    # попавшийся»: с включённым контролем картинок в ответе несколько.
    outs = entry.get("outputs", {})
    imgs = outs.get("12", {}).get("images") or []
    shot = imgs[-1] if imgs else None
    if not shot:
        raise RuntimeError("ComfyUI не вернул картинку")

    # Карту глубины кладём рядом со скриптом — по образцу _last_mask.png:
    # посмотреть глазами, что модель вообще разглядела за объём.
    for node, fname, what in (("83", "_last_depth.png", "карту глубины"),
                              ("93", "_last_color.png", "цветовую сетку")):
        im0 = (outs.get(node, {}).get("images") or [None])[0]
        if not im0:
            continue
        try:
            with open(os.path.join(HERE, fname), "wb") as f:
                f.write(comfy_view(im0))
        except Exception as e:
            print(f"  {what} не сохранил:", e, flush=True)

    res = Image.open(io.BytesIO(comfy_view(shot))).convert("RGB")

    # Вырезка по контуру: альфа = маска с растушёвкой под mask_blend,
    # прямоугольник = bbox + запас, иначе обрежем растушёванный край и получим шов.
    # запас = ровно растушёвка: при blend=0 вырезка точно по выделению,
    # видно любое смещение
    m = blend
    rect = (max(0, x0 - m), max(0, y0 - m), min(W, x1 + m), min(H, y1 + m))
    alpha = blend_alpha(mask, blend, shape)
    cut = res.crop(rect).convert("RGBA")
    cut.putalpha(alpha.crop(rect))

    # Photoshop сообщает границы НЕПРОЗРАЧНЫХ пикселей, а не края картинки.
    # Растушёвка оставляет по краям прозрачную каёмку, поэтому говорим панели,
    # где внутри картинки начинается непрозрачное — иначе слой уедет на её ширину.
    abox = cut.getchannel("A").getbbox()
    ax, ay = (abox[0], abox[1]) if abox else (0, 0)

    secs = round(time.time() - t0, 1)
    print(f"  готово за {secs}с -> слой {cut.size[0]}x{cut.size[1]} @({rect[0]},{rect[1]})"
          f" | непрозрачное с ({ax},{ay})", flush=True)
    return {
        "image": base64.b64encode(to_png(cut)).decode(),
        "x": rect[0], "y": rect[1],
        "content_x": rect[0] + ax, "content_y": rect[1] + ay,
        "width": cut.size[0], "height": cut.size[1],
        "seed": seed, "seconds": secs, "file": shot.get("filename"),
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/status"):
            self._send(200, dict(STATE))
        elif self.path.startswith("/lists"):
            try:
                self._send(200, get_lists())
            except Exception as e:
                self._send(500, {"error": str(e)})
        elif self.path.startswith("/ping"):
            try:
                comfy_get("/system_stats")
            except Exception:
                return self._send(200, {"ok": True, "comfy": False,
                                        "error": "ComfyUI не запущен на 8188"})
            miss = missing_nodes()
            self._send(200, {"ok": True, "comfy": True, "missing": miss})
        else:
            self._send(404, {"error": "нет такого адреса"})

    def do_POST(self):
        if self.path.startswith("/interrupt"):
            try:
                comfy_post_raw("/interrupt")
                print("  ОТМЕНА от панели", flush=True)
                self._send(200, {"ok": True})
            except Exception as e:
                self._send(500, {"error": str(e)})
            return
        if not self.path.startswith("/inpaint"):
            return self._send(404, {"error": "нет такого адреса"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            p = json.loads(self.rfile.read(n).decode())
        except Exception as e:
            return self._send(400, {"error": f"кривой запрос: {e}"})
        print(f"[{time.strftime('%H:%M:%S')}] запрос на inpaint", flush=True)
        try:
            self._send(200, run_inpaint(p))
        except Exception as e:
            if str(e) == "прервано":
                # обычная отмена, а не поломка — незачем пугать простынёй
                print("  отменено пользователем", flush=True)
            else:
                traceback.print_exc()
                print("  ОШИБКА:", e, flush=True)
            self._send(500, {"error": str(e)})

    def log_message(self, *a):
        pass


class Server(ThreadingHTTPServer):
    # Иначе Windows пустит ВТОРОЙ мост на тот же порт, и запросы будут
    # случайно уходить то в один, то в другой. Пусть лучше ругается.
    allow_reuse_address = False


if __name__ == "__main__":
    if not os.path.exists(GRAPH):
        sys.exit(f"Нет файла графа: {GRAPH}")
    try:
        srv = Server(("127.0.0.1", PORT), Handler)
    except OSError:
        sys.exit(f"Порт {PORT} уже занят — похоже, мост уже запущен в другом окне.\n"
                 f"Закрой то окно или пользуйся им.")
    threading.Thread(target=ws_listen, daemon=True).start()
    print(f"Мост Photoshop <-> ComfyUI слушает http://127.0.0.1:{PORT}")
    print(f"ComfyUI ожидается на {COMFY}. Настройки: config_ps.txt")
    print("Закрыть окно = выключить мост.\n")
    srv.serve_forever()
