# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A **fully self-contained, portable** ComfyUI image-generation kit with a thin custom layer at the repo root. Stock ComfyUI (`ComfyUI/`, `python_embeded/`, `update/`) is the engine; everything interesting lives in the root-level scripts. Output is tuned to match a specific tensor.art recipe (A1111/Forge-style sampling parity).

The whole folder — engine, embedded Python, custom nodes, **and the models** — is meant to be copied to a laptop or handed to a friend on a drive and just work, with no install step. That property is the point of the project and constrains most design decisions below.

## Как здесь принято объяснять (читать до всего остального)

Правило одно: **сначала скажи, кто что с чем делает.** Как «мама мыла раму». Есть действующее лицо, есть действие, есть предмет — и понимать становится нечего, всё уже понятно.

Понимание умирает там, где действующее лицо выкинули: «осуществляется компиляция исходного кода». Кто осуществляет? Что с чем? Формально предложение то же, а понять нечего.

Сложное всегда состоит из простого, и его можно разобрать до простых вещей:

> «скомпилировать» → берём текст, который написал программист, и делаем из него значок, на который можно нажать

Первое понимает примерно один человек из ста, второе — каждый второй. Разница не в два раза, а в пятьдесят. При этом компиляция не перестала быть компиляцией — ни слова неправды не сказано.

**Жаргон выбирается по слушателю, а не по привычке — и слушателя не надо додумывать.** Автор проекта — художник: он придумал этот инструмент и точно знает, что тот делает, но слова из кода ему никто объяснять не обязан был. Поэтому термин можно пускать в дело только после того, как один раз объяснил его простыми словами. «Он часто встречается в коде» — это не основание считать, что собеседник его знает.

Как это выглядит на нашем материале:

- **плохо:** «дисперсия лапласиана 236, ВЧ-доля спектра 0.3501»
- **хорошо:** «чёткая чёрная обводка и меньше грязи в плоских заливках»
- **плохо:** «updater скачивает манифест, сверяет sha256 и применяет дельту»
- **хорошо:** «программа сходила в интернет, посмотрела, что нового вышло, сравнила с тем, что у тебя стоит, и доложила: есть одно обновление. Перед тем как менять файлы, она откладывает старые в сторонку — если новое не понравится, вернём обратно одной кнопкой»

Второй пример показывает, зачем это нужно не только читателю: **в простой формулировке видно устройство механизма.** Сходила → сравнила → доложила → отложила старое → заменила. Это уже готовый список шагов. Если объяснить просто не получается — обычно значит, что механизм ещё не продуман, а не что слова не подобрались.

Проверка перед тем, как что-то написать или предложить: можешь простыми словами сказать, **зачем** оно и **что даёт**? Если нет — понимание неполное, и сначала надо разобраться, а не подбирать термины. Как оно устроено внутри, иногда действительно объясняется только сложно — это нормально. Смысл — никогда.

## Portability is the invariant

Treat these as hard rules; violating any one of them silently breaks the "copy the folder and it works" promise:

- **Everything path-related is relative to the script.** Every root script computes `HERE = os.path.dirname(os.path.abspath(__file__))` and derives `OUTROOT`/`INPUTDIR` from it. Never hardcode a drive letter or absolute path.
- **Models live inside the repo** at `ComfyUI/models/` (checkpoints, loras, vae, controlnet, ipadapter, clip_vision — ~15 GB). There is deliberately **no `extra_model_paths.yaml`**; do not add one to point at an external install.
- **No install step, ever.** `python_embeded/` already has everything the root scripts need (PIL, numpy, scipy, websocket-client on Python 3.13). If a change needs a new dependency, that dependency has to be vendored into `python_embeded/` — prefer solving it with the stdlib instead.
- **Never assume a specific model file exists.** Resolve names against the live server (`/object_info`) and fail with a message listing what *is* available — see `resolve_model()` in `ps_bridge.py` and the ControlNet lookup in `run_depth.py`/`run_canny.py`.
- **Degrade, don't crash.** No NVIDIA GPU → ComfyUI falls back to CPU on its own. VAE not specified → take it from the checkpoint rather than requiring a separate file.

## Commands

Run everything with the embedded interpreter `python_embeded\python.exe`; there is no system Python guaranteed. No build, lint, or test suite — this is a runtime/scripting project.

**Start the server first** (all render scripts are HTTP clients and do nothing without it):

```
ЗАПУСК.exe          — точка входа: обновления + мост + ComfyUI
```
The EXE is deliberately dumb — it only calls `python_embeded\python.exe launcher.py`. All behaviour lives in `launcher.py`: read `ВЕРСИЯ.txt`, ask GitHub what's new, apply pending patches, then start the Photoshop bridge in a second window (port 8189) and ComfyUI on 8188 with `--auto-launch`, teeing the server log to `logs\comfyui_server.log`.

`ЗАПУСК_ComfyUI.bat` still exists and does the launch half without the update check. Manual equivalents:
`.\python_embeded\python.exe launcher.py [--без-обновлений]`
`.\python_embeded\python.exe -s ComfyUI\main.py --port 8188 --auto-launch`

**Render** (server must already be up). Each `.bat` is a thin wrapper over its script; the optional first arg is an integer seed (omitted = random, and with `count>1` a given seed increments per image while a random one is re-rolled):

| Launcher | Script | Config | Purpose |
|---|---|---|---|
| `РЕНДЕР.bat` | `run_workflow.py` | `config.txt` | plain txt2img |
| `РЕНДЕР_ПОЗА.bat` | `run_depth.py` | `config.txt` (`depth_*`) | ControlNet depth — copy a pose |
| `РЕНДЕР_КОНТУР.bat` | `run_canny.py` | `config.txt` (`canny_*`) | ControlNet canny — copy line art |
| `РЕНДЕР_IP.bat` | `run_workflow_ip.py` | `config_ip.txt` | IPAdapter — blend in a reference |
| `РЕНДЕР_REF.bat` | `run_workflow_ref.py` | `config_ref.txt` | reference-only |
| `МОСТ_PS.bat` → `ps_bridge.bat` | `ps_bridge.py` | `config_ps.txt` | Photoshop inpaint bridge (port 8189) |
| `СОБРАТЬ_ЛОГИ.bat` | `_diag.py` | — | collect diagnostics + zip `logs\` to Desktop |
| `ОТКАТ.bat` | `launcher.py --откат` | — | undo the last applied patch |

`ПОЗА`/`КОНТУР` also accept an image dragged onto the `.bat`. All scripts read the prompt from `prompt.txt` and `negative.txt`.

**Update ComfyUI code**: `update\update_comfyui.bat`. The `_and_python_dependencies` variant only on dependency breakage — it can disturb the vendored `python_embeded`.

## Architecture

### Render scripts share one skeleton

`run_workflow.py`, `run_workflow_ip.py`, `run_workflow_ref.py`, `run_depth.py`, `run_canny.py` are near-copies of each other by design (each one stays readable and independently editable). The common shape:

1. `import _log; _log.start()` — tee stdout/stderr to `logs\<script>_<timestamp>.log`.
2. Parse a `key = value` config (`#` comments) into a lowercased dict, read `prompt.txt`/`negative.txt`.
3. Build the graph, POST it to `http://127.0.0.1:8188/prompt`, poll `/history/{id}` every 2s with a 600s timeout.
4. Print each finished file, then `os.startfile()` the output folder **once, after all images are done**.

Two ways of building the graph coexist:
- **Template-patching** (`run_workflow.py`, `_ip`, `_ref`): deep-copy `workflow_api*.json` per image and patch node inputs by matching `class_type`.
- **Inline construction** (`run_depth.py`, `run_canny.py`): the whole graph is a dict literal in `build(seed)`, no template file.

### The A1111/Forge parity layer

The reason this graph exists at all. It depends on custom nodes in `ComfyUI/custom_nodes/`:

- **`ComfyUI_smZNodes`** → the `smZ Settings` node. Every render script queries the live `/object_info` to fill **all** of that node's optional inputs with their declared defaults, then applies a curated override set: `RNG=cpu`, `ENSD=31337`, `eta=1.0`, `enable_emphasis=True`, `Use CFGDenoiser`, `sgm_noise_multiplier`. Three of these read env vars for experiments: `RNG`, `CFGD`, `SGM`. Reading defaults off the live server rather than hardcoding them is what keeps the graph working across smZNodes updates — keep it that way.
- **`ComfyUI_ADV_CLIP_emb`** → `BNK_CLIPTextEncodeAdvanced` with `weight_interpretation: A1111`, `token_normalization: none`.
- **`comfyui_lora_tag_loader`** → `LoraTagLoader`, so loras are inline `<lora:NAME:WEIGHT>` tags in A1111 prompt syntax rather than graph nodes.
- Also present: `comfyui_controlnet_aux` (depth/canny preprocessors), `ComfyUI_IPAdapter_plus`, `ComfyUI-Inpaint-CropAndStitch`, `comfyui-inpaint-nodes`, `ComfyUI-Manager`, `ComfyUI_experiments`.

### Node-id contracts (fragile — preserve when editing graphs)

- In `workflow_api.json`, `workflow_api_ip.json`, `workflow_api_ref.json`: the two text encoders are told apart **by hardcoded node id** — `"10051"` = positive, `"10052"` = negative. Everything else is matched by `class_type`. Regenerating a template without preserving these ids means the prompt is silently never applied.
- In `inpaint_onlymasked_api.json`, `ps_bridge.py` patches **by numeric id**: `1` checkpoint, `2` LoraTagLoader, `4` VAELoader (dropped entirely when no VAE is configured, with `50`/`11` repointed to the checkpoint's VAE output), `5`/`6` positive/negative, `7` image, `70` mask, `60` InpaintCropImproved, `10` KSampler, `61` InpaintStitchImproved.

### ControlNet pipelines (depth / canny)

Donor image resolution order: CLI arg → `depth_image`/`canny_image` in `config.txt` → newest image in `depth\donor\` / `canny\donor\`. The donor is copied into `ComfyUI\input\` because ComfyUI only loads images from there. The generated map is copied to `depth\map.png` / `canny\map.png` (overwritten each run) and **deleted from the output folder** so it doesn't accumulate.

By default the canvas is refitted to the donor's aspect ratio (`depth_fit`/`canny_fit = donor`), preserving the pixel budget `width*height` from config and rounding to multiples of 64 — a mismatched aspect stretches the control map and breaks anatomy. Set `= config` to force the configured size.

The ControlNet checkpoint is **discovered at runtime** by searching `/object_info/ControlNetLoader` for a name containing `depth`/`canny` + `sdxl`, never hardcoded.

### Photoshop bridge

`ComfyInpaint_panel/` is an Adobe UXP panel (manifest v4, PS 23.3+) — `index.html` + `main.js`, no build step. Its manifest whitelists exactly `http://127.0.0.1:8189`, so **the bridge port is baked into the panel**; changing `PORT` in `ps_bridge.py` requires editing `manifest.json` too.

`ps_bridge.py` is a `ThreadingHTTPServer` on 8189 (with `allow_reuse_address = False`, so a second bridge fails loudly instead of stealing requests). API: `GET /status` (live progress), `GET /lists` (models/loras/VAEs/embeddings, read from the server so the panel never shows files ComfyUI can't load), `GET /ping` (is ComfyUI up + which required custom nodes are missing), `POST /inpaint`, `POST /interrupt`. A background thread holds a websocket to ComfyUI to receive progress, reconnecting on drop.

Subtleties worth preserving in `run_inpaint()`:
- Photoshop sends the selection as a **patch** (raw pixels + `left`/`top`/`canvas_width`/`canvas_height`), not a full-canvas image; `to_image()` pastes it back to its place on a full canvas. A mask whose size doesn't match the canvas is a hard error — resizing it would silently produce mush.
- `blend_alpha()` feathers **outward only**: the alpha plateau reaches exactly the selection contour and all falloff happens outside it. The naive expand→blur the node itself uses eats into the selection edge.
- `context_factor()` converts "N pixels of context" into the multiplier the crop node actually wants.
- The returned crop is `bbox + blend` px, and the response reports both the rectangle origin (`x`/`y`) and where opaque pixels start inside it (`content_x`/`content_y`) — Photoshop positions layers by opaque bounds, so without the latter the layer lands offset by the feather width.
- `_last_mask.png` is written next to the script each run for eyeballing mask alignment.

### Update mechanism (`launcher.py`)

Patches are plain zips listed in `patches/index.json`, fetched anonymously from `raw.githubusercontent.com/dreizehntephantom/comfy-pocket/main/patches/` (the repo is public precisely so updating never asks for a password). Files inside the zip sit at paths relative to the build root; everything in a patch is applied — there is no "optional" tier.

Invariants worth preserving:
- **Stdlib only.** Adding a dependency here would break portability. `POCKET_URL` overrides the base URL for testing against a fake server.
- **Zip entries are untrusted.** `safe_members()` rejects `..`, drive letters, and anything under `NEVER_TOUCH` (output, input, refs, donors, logs, backups) — a downloaded archive must not be able to write outside the build or over the user's images.
- **Back up before replacing.** Originals go to `бэкап\до_обновления_NNN_<timestamp>\` with a `что_было.json` recording what was replaced vs newly added; `rollback()` uses it to restore and to delete additions.
- **A rolled-back patch is never reinstalled.** Its number goes into `бэкап\не_ставить.txt`, and `update()` stops at the first rejected patch rather than skipping over it — later patches assume the earlier one is present.
- `ЧТО_ДЕЛАТЬ.txt` inside a zip is shown to the user, never written to disk.

`сборка\` holds the EXE build (icon, stub, build script). Rebuilding should be rare — see `сборка\ЧТО_ЗДЕСЬ.txt` for why the EXE is deliberately empty.

### Logging and support flow

`_log.py` tees stdout+stderr into `logs\` and installs an excepthook, so a traceback survives even if the console window blinks shut. It deliberately does not import torch (these scripts are HTTP clients; loading torch would slow every run). `_diag.py` collects OS/RAM/disk/torch/CUDA/GPU info, pings the server, lists installed models and all four configs, then zips `logs\` to the Desktop — the intended flow is a non-technical user running `СОБРАТЬ_ЛОГИ.bat` and sending the zip back.

## Conventions / gotchas

- **`.bat` bodies must be ASCII** even though their filenames are Cyrillic: cmd reads batch bodies in chunks in a single-byte codepage, and a chunk boundary landing mid-UTF-8-character breaks the commands. Russian text belongs in Python output (which is fine after `chcp 65001` + `PYTHONIOENCODING=utf-8`). Some older launchers (`РЕНДЕР.bat`) still contain cp1251 Russian in `echo` lines — follow the newer ones (`РЕНДЕР_ПОЗА.bat`) and keep new bat bodies English.
- Python sources are UTF-8 with Russian comments and Russian user-facing output; keep that voice — the end users are non-technical.
- `ComfyUI/` and each of the nine `custom_nodes/*` are **their own git repos**. A repo at the root must not try to track their contents.
- `run_depth.py:151` and `run_canny.py:157` still tell the user to look in `D:\Illustrious\webui\models\ControlNet\` when no ControlNet model is found — a leftover from the pre-portable era. The correct location is now `ComfyUI\models\controlnet\`.
- `negative_original.txt` is a kept-aside backup; `negative.txt` is the live one. `Ivy.txt`, `КОНТУР_инструкция.txt`, `ПОЗА_инструкция.txt` are user-facing notes, not code.
- `README_VERY_IMPORTANT.txt` is stock ComfyUI's readme, not ours — it describes `run_nvidia_gpu.bat`/`run_cpu.bat` (also stock) and mentions `extra_model_paths.yaml`, which contradicts the portability rules above.
- Output goes to `ComfyUI\output\YYYY-MM-DD\` with a per-pipeline prefix: `sync`, `depth`, `canny`, `ipadapter`, `refonly`.
