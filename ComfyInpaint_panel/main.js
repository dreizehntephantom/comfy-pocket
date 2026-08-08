// Панель: выделение в Photoshop -> мост -> ComfyUI -> новый слой.
// Мост поднимается вместе с ComfyUI (или вручную: ps_bridge.bat).

const { app, core, action, imaging } = require("photoshop");
const uxp = require("uxp");
const fs = uxp.storage.localFileSystem;

const BRIDGE = "http://127.0.0.1:8189";
const NO_BRIDGE = "Мост не отвечает.\nЗапусти ComfyUI — мост поднимется вместе с ним.\n" +
                  "Или вручную: ps_bridge.bat рядом с ComfyUI.";
const $ = (id) => document.getElementById(id);

function say(msg, cls) {
  const el = $("status");
  el.textContent = msg;
  el.className = cls || "";
}

// ---- переходники к Spectrum-виджетам ----
// У sp-picker выбор живёт и в .value, и в атрибуте selected у пункта. Читаем и
// пишем через эти две функции, чтобы остальной код не знал про эту разницу.
const isPicker = (el) => el && el.tagName && el.tagName.toLowerCase() === "sp-picker";

function getVal(id) {
  const el = $(id);
  if (!el) return "";
  let v = el.value;
  if ((v === undefined || v === null) && isPicker(el)) {
    const sel = el.querySelector("sp-menu-item[selected]");
    v = sel ? sel.getAttribute("value") : "";
  }
  return v === undefined || v === null ? "" : String(v);
}

function setVal(id, v) {
  const el = $(id);
  if (!el) return;
  // Строкой, всегда: sp-textfield молча обнуляется, если положить число
  if (isPicker(el)) pick(el, v);
  else el.value = v === undefined || v === null ? "" : String(v);
}

// "0,9" -> 0.9 : на русской раскладке запятая, а parseFloat обрывает число на ней
function num(v, dflt) {
  const x = parseFloat(String(v).trim().replace(",", "."));
  return isFinite(x) ? x : dflt;
}

// ---- прогресс прямо в кнопке ----
let poller = null;
let cancelled = false;

function setProgress(pct, text) {
  const w = Math.max(0, Math.min(100, pct)) + "%";
  $("goFill").style.width = w;
  $("goBar").style.width = w;
  $("goText").textContent = text;
}

// Проценты настоящие: ComfyUI по вебсокету говорит мосту "шаг 7 из 25",
// мост держит это в /status, панель раз в полсекунды спрашивает.
function startPoll(variant, count) {
  stopPoll();
  poller = setInterval(async () => {
    try {
      const s = await (await fetch(BRIDGE + "/status")).json();
      if (s.max > 0) {
        const overall = ((variant + s.value / s.max) / count) * 100;
        setProgress(overall, count > 1
          ? `${Math.round(overall)}%  ·  ${variant + 1}/${count}`
          : `${Math.round(overall)}%`);
      } else {
        setProgress((variant / count) * 100, "подготовка...");
      }
    } catch (e) { /* мост занят — не беда, спросим через полсекунды */ }
  }, 500);
}

function stopPoll() {
  if (poller) clearInterval(poller);
  poller = null;
}

// #go — свой div, а не sp-button: в родную кнопку заливку не положить,
// её рисует система и вложенные полоски игнорирует.
let busy = false;

function setBusy(b) {
  busy = b;
  $("go").classList.toggle("busy", b);
  $("cancel").style.display = b ? "inline-flex" : "none";
}

function idleButton() {
  stopPoll();
  setProgress(0, "ГЕНЕРАЦИЯ");
  setBusy(false);
}

const B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

function toBase64(bytes) {
  let out = "";
  const n = bytes.length;
  for (let i = 0; i < n; i += 3) {
    const a = bytes[i], b = i + 1 < n ? bytes[i + 1] : 0, c = i + 2 < n ? bytes[i + 2] : 0;
    out += B64[a >> 2];
    out += B64[((a & 3) << 4) | (b >> 4)];
    out += i + 1 < n ? B64[((b & 15) << 2) | (c >> 6)] : "=";
    out += i + 2 < n ? B64[c & 63] : "=";
  }
  return out;
}

function fromBase64(str) {
  const clean = str.replace(/[^A-Za-z0-9+/]/g, "");
  const n = clean.length;
  const out = new Uint8Array((n * 3) >> 2);
  let p = 0, buf = 0, bits = 0;
  for (let i = 0; i < n; i++) {
    buf = (buf << 6) | B64.indexOf(clean[i]);
    bits += 6;
    if (bits >= 8) {
      bits -= 8;
      out[p++] = (buf >> bits) & 0xff;
    }
  }
  return out.subarray(0, p);
}

// Photoshop после вставки слоя делает выделением его прямоугольник. Чтобы твой
// контур не терялся, прячем его во временный канал и возвращаем обратно.
const SEL_CHANNEL = "comfy_inpaint_sel";

async function saveSelection() {
  await action.batchPlay([{
    _obj: "duplicate",
    _target: [{ _ref: "channel", _property: "selection" }],
    name: SEL_CHANNEL,
    _isCommand: true,
  }], { modalBehavior: "execute" });
}

async function restoreSelection() {
  await action.batchPlay([{
    _obj: "set",
    _target: [{ _ref: "channel", _property: "selection" }],
    to: { _ref: "channel", _name: SEL_CHANNEL },
    _isCommand: true,
  }], { modalBehavior: "execute" });
  await dropSelChannel();
}

async function dropSelChannel() {
  await action.batchPlay([{
    _obj: "delete",
    _target: [{ _ref: "channel", _name: SEL_CHANNEL }],
    _isCommand: true,
  }], { modalBehavior: "execute" });
}

// Если что-то сорвалось — не оставляем временный канал в документе
async function cleanupSelChannel() {
  try {
    await core.executeAsModal(async () => { await dropSelChannel(); },
      { commandName: "Убрать временный канал" });
  } catch (e) { /* канала нет — и хорошо */ }
}

// Границы выделения — тем же способом, что и stable.art
async function selectionBounds() {
  const r = await action.batchPlay([{
    _obj: "get",
    _target: [{ _property: "selection" }, { _ref: "document", _id: app.activeDocument.id }],
    _options: { dialogOptions: "dontDisplay" },
  }], {});
  const s = r[0] && r[0].selection;
  if (!s || s.left === undefined) return null;
  return {
    left: Math.round(s.left._value),
    top: Math.round(s.top._value),
    right: Math.round(s.right._value),
    bottom: Math.round(s.bottom._value),
  };
}

// Склейка холста + маска выделения, сырыми пикселями
async function grabPixels(bounds) {
  const doc = app.activeDocument;
  const W = doc.width, H = doc.height;
  const full = { left: 0, top: 0, right: W, bottom: H };

  // Photoshop возвращает СВОИ размеры, а не те, что просили: getSelection отдаёт
  // только лоскут выделения. Размер и смещение берём из ответа, не гадаем.
  function pack(res) {
    const id = res.imageData;
    const sb = res.sourceBounds || {};
    let left = Number(sb.left), top = Number(sb.top);

    // Если Photoshop смещение не сказал — вычисляем его сами по границам
    // выделения. Тихо подставить 0,0 нельзя: маска уедет в угол холста.
    if (!isFinite(left) || !isFinite(top)) {
      if (bounds && id.width === bounds.right - bounds.left &&
                    id.height === bounds.bottom - bounds.top) {
        left = bounds.left; top = bounds.top;
      } else if (id.width === W && id.height === H) {
        left = 0; top = 0;
      } else {
        throw new Error(
          `Photoshop отдал лоскут ${id.width}x${id.height} без координат, ` +
          `а выделение ${bounds ? (bounds.right - bounds.left) + "x" + (bounds.bottom - bounds.top) : "?"}. ` +
          `Не знаю, куда его класть — скажи это Клоду.`);
      }
    }
    return {
      bytes: id.getData({ chunky: true }),
      meta: {
        width: id.width, height: id.height, components: id.components,
        left: Math.round(left), top: Math.round(top),
        canvas_width: W, canvas_height: H,
      },
      imageData: id,
    };
  }

  const px = pack(await imaging.getPixels({
    documentID: doc.id, sourceBounds: full, componentSize: 8, applyAlpha: false,
  }));
  const imgBytes = await px.bytes;
  px.imageData.dispose();

  const sel = pack(await imaging.getSelection({ documentID: doc.id, sourceBounds: full }));
  const mskBytes = await sel.bytes;
  sel.imageData.dispose();

  const image = Object.assign({ data: toBase64(imgBytes) }, px.meta);
  const mask = Object.assign({ data: toBase64(mskBytes) }, sel.meta);
  console.log("image:", JSON.stringify(px.meta), imgBytes.length);
  console.log("mask:", JSON.stringify(sel.meta), mskBytes.length);
  return { image, mask };
}

// Вставить PNG новым слоем и сдвинуть на своё место (рецепт stable.art).
// x,y — куда должен попасть ПЕРВЫЙ НЕПРОЗРАЧНЫЙ пиксель, а не край картинки:
// Photoshop меряет слой по непрозрачному, а растушёвка оставляет прозрачную каёмку.
async function placeResult(b64png, x, y, name) {
  const tmp = await fs.getTemporaryFolder();
  const file = await tmp.createFile("comfy_inpaint_result.png", { overwrite: true });
  await file.write(fromBase64(b64png), { format: uxp.storage.formats.binary });
  const token = fs.createSessionToken(file);

  await core.executeAsModal(async (ctx) => {
    const hist = await ctx.hostControl.suspendHistory({
      documentID: app.activeDocument.id,
      name: "ComfyUI inpaint",
    });
    const r = await action.batchPlay([
      { _obj: "placeEvent", target: { _path: token, _kind: "local" }, linked: false, _isCommand: true },
      {
        _obj: "multiGet",
        _target: { _ref: "layer", _enum: "ordinal", _value: "targetEnum" },
        extendedReference: [["bounds", "layerID"]],
        options: { failOnMissingProperty: false, failOnMissingElement: false },
      },
    ], { modalBehavior: "execute" });

    const b = r[1].bounds;
    await action.batchPlay([{
      _obj: "move",
      _target: [{ _ref: "layer", _enum: "ordinal", _value: "targetEnum" }],
      to: {
        _obj: "offset",
        horizontal: { _unit: "pixelsUnit", _value: x - b.left._value },
        vertical: { _unit: "pixelsUnit", _value: y - b.top._value },
      },
      _isCommand: true,
    }], { modalBehavior: "execute" });

    // растеризуем, чтобы слой можно было стирать и мешать как обычный
    await action.batchPlay([{
      _obj: "rasterizeLayer",
      _target: [{ _ref: "layer", _enum: "ordinal", _value: "targetEnum" }],
      _isCommand: true,
    }], { modalBehavior: "execute" });

    if (name) {
      await action.batchPlay([{
        _obj: "set",
        _target: [{ _ref: "layer", _enum: "ordinal", _value: "targetEnum" }],
        to: { _obj: "layer", name: name },
        _isCommand: true,
      }], { modalBehavior: "execute" });
    }

    await ctx.hostControl.resumeHistory(hist);
  }, { commandName: "ComfyUI inpaint" });
}

async function generate() {
  if (busy) return;          // div-кнопку нельзя "disabled", сторожим флагом
  setBusy(true);
  cancelled = false;
  let selSaved = false;
  try {
    if (!app.documents.length) {
      say("Нет открытого документа.", "err");
      return;
    }

    say("Читаю выделение...");
    const bounds = await selectionBounds();
    if (!bounds) {
      say("Ничего не выделено. Выдели область любым инструментом\n(лассо, палочка, прямоугольник) и жми снова.", "err");
      return;
    }
    const bw = bounds.right - bounds.left, bh = bounds.bottom - bounds.top;

    // параметры проверяем ДО того, как трогать документ
    let denoise = num(getVal("denoise"), 0.6);
    if (denoise <= 0 || denoise > 1) {
      say(`Denoise = ${denoise} — так не бывает. Нужно от 0.05 до 1.0\n` +
          `(0.4-0.6 подправить, 0.75-1.0 переодеть).`, "err");
      return;
    }
    setVal("denoise", denoise);

    await saveSettings();   // запомним выбор до генерации, а не после

    say("Забираю пиксели...");
    let grabbed;
    await core.executeAsModal(async () => {
      grabbed = await grabPixels(bounds);
      await saveSelection();   // вернём его после вставки слоя
      selSaved = true;
    }, { commandName: "Забрать пиксели для ComfyUI" });

    const payload = {
      image: grabbed.image,
      mask: grabbed.mask,
      bbox: [bounds.left, bounds.top, bounds.right, bounds.bottom],
      context_px: parseInt(getVal("context"), 10) || 64,
      target: parseInt(getVal("target"), 10) || 0,
      mask_blend: parseInt(getVal("blend"), 10) || 0,
      blend_shape: getVal("shape") || "gauss",
      denoise: denoise,
      prompt: getVal("prompt"),
      negative: getVal("negative"),
      model: getVal("model"),                      // "" = из config_ps.txt
      vae: getVal("vae"),                          // "" = взять из модели
      lora: getVal("lora"),                        // "" = без лоры
      lora_weight: num(getVal("loraWeight"), 0.8),
      neg_embedding: getVal("embedding"),          // "" = без эмбеддинга
      steps: Math.max(1, Math.round(num(getVal("steps"), 25))),
      cfg: num(getVal("cfg"), 5),
    };
    const seedText = getVal("seed").trim();
    const baseSeed = seedText ? parseInt(seedText, 10) : null;
    const count = parseInt(getVal("count"), 10) || 1;

    // Пиксели забраны ОДИН раз: каждый вариант рисуется по исходному холсту,
    // иначе второй увидит на нём первый и станет рисовать поверх нарисованного.
    const t0 = Date.now();
    const seeds = [];
    say(`Рисую ${bw}x${bh}, контекст ${payload.context_px}px`);

    for (let i = 0; i < count; i++) {
      const p = Object.assign({}, payload);
      if (baseSeed !== null) p.seed = baseSeed + i;   // задан сид — идём подряд

      startPoll(i, count);
      const resp = await fetch(BRIDGE + "/inpaint", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(p),
      });
      const data = await resp.json();
      stopPoll();

      if (!resp.ok) {
        // отмена — это не поломка, мост говорит про неё отдельно
        if (cancelled || String(data.error || "").includes("прервано")) {
          say(`Отменено.${seeds.length ? ` Готовые слои (${seeds.length}) на месте.` : ""}`);
        } else {
          say(`Мост ответил ошибкой${count > 1 ? ` на варианте ${i + 1}` : ""}:\n` +
              (data.error || resp.status), "err");
        }
        return;
      }

      setProgress(((i + 1) / count) * 100, "кладу слой...");
      const cx = data.content_x !== undefined ? data.content_x : data.x;
      const cy = data.content_y !== undefined ? data.content_y : data.y;
      await placeResult(data.image, cx, cy, `inpaint ${data.seed}`);
      seeds.push(data.seed);

      if (cancelled) {
        say(`Отменено. Готовые слои (${seeds.length}) на месте.`);
        return;
      }
    }

    const secs = ((Date.now() - t0) / 1000).toFixed(1);
    say(count > 1
      ? `Готово за ${secs}с — ${count} слоя(ёв) стопкой, имя = сид.\n` +
        `Сравнивай глазиком в панели слоёв, лишние удали.`
      : `Готово за ${secs}с. Сид: ${seeds[0]}\nВыделение на месте — можно жать ещё раз.`, "ok");
  } catch (e) {
    const msg = String(e && e.message ? e.message : e);
    if (msg.includes("Failed to fetch") || msg.includes("NetworkError")) {
      say(NO_BRIDGE, "err");
    } else {
      say("Сбой: " + msg, "err");
    }
    console.error(e);
  } finally {
    // Выделение возвращаем в любом случае — и после всех вариантов, и если
    // сорвались на полпути. Заодно тут же убирается временный канал.
    if (selSaved) {
      try {
        await core.executeAsModal(async () => { await restoreSelection(); },
          { commandName: "Вернуть выделение" });
      } catch (e) {
        console.error("не вернул выделение:", e);
        await cleanupSelChannel();
      }
    }
    idleButton();
  }
}

$("cancel").addEventListener("click", async () => {
  cancelled = true;
  $("cancel").disabled = true;
  setProgress(100, "отменяю...");
  try {
    await fetch(BRIDGE + "/interrupt", { method: "POST" });
  } catch (e) {
    console.error("не смог отменить:", e);
  }
  $("cancel").disabled = false;
});

// ---- память панели: переживает перезапуск Photoshop ----
// Храним файлом в папке данных плагина: гарантированный API, в отличие от
// localStorage, которого в UXP может не оказаться.
const REMEMBER = ["prompt", "negative", "model", "vae", "lora", "loraWeight", "embedding",
                  "context", "target", "blend", "shape", "denoise", "steps", "cfg", "count"];

// sp-textfield не читает value= из разметки — умолчания расставляем из кода
const DEFAULTS = { denoise: "0.6", loraWeight: "0.8", steps: "25", cfg: "5" };

async function loadSettings() {
  try {
    const folder = await fs.getDataFolder();
    const entries = await folder.getEntries();
    const f = entries.find((e) => e.name === "settings.json");
    if (!f) return {};
    return JSON.parse(await f.read()) || {};
  } catch (e) {
    console.error("настройки не прочитались:", e);
    return {};
  }
}

async function saveSettings() {
  try {
    const obj = {};
    for (const id of REMEMBER) {
      if ($(id)) obj[id] = getVal(id);
    }
    const folder = await fs.getDataFolder();
    const f = await folder.createFile("settings.json", { overwrite: true });
    await f.write(JSON.stringify(obj));
  } catch (e) {
    console.error("настройки не сохранились:", e);
  }
}

function fill(picker, items, noneLabel, strip) {
  const menu = picker.querySelector("sp-menu");
  if (!menu) return;
  menu.innerHTML = "";
  const add = (value, text) => {
    const it = document.createElement("sp-menu-item");
    it.setAttribute("value", value);
    it.textContent = text;
    menu.appendChild(it);
  };
  add("", noneLabel);
  for (const it of items) {
    add(it, strip ? it.replace(/\.(safetensors|ckpt|pt)$/i, "") : it);
  }
}

// Выбрать значение, молча пережив то, что такой лоры больше нет в папке
function pick(picker, value) {
  if (value === undefined || value === null) return;
  const items = Array.from(picker.querySelectorAll("sp-menu-item"));
  const hit = items.find((o) => o.getAttribute("value") === String(value));
  if (!hit) return;
  items.forEach((o) => o.removeAttribute("selected"));
  hit.setAttribute("selected", "");
  try { picker.value = String(value); } catch (e) { /* хватит и атрибута */ }
}

async function init() {
  // Умолчания и память — первым делом: если мост не поднят, поля всё равно
  // должны быть заполнены, а не пустовать.
  for (const [id, v] of Object.entries(DEFAULTS)) setVal(id, v);
  const saved = await loadSettings();
  const applySaved = () => {
    for (const id of REMEMBER) {
      if ($(id) && saved[id] !== undefined) setVal(id, saved[id]);
    }
    showBlend();
  };
  applySaved();

  for (const id of REMEMBER) {
    const el = $(id);
    if (!el) continue;
    el.addEventListener("change", saveSettings);
    el.addEventListener("input", saveSettings);
  }

  let lists = null;
  try {
    const r = await fetch(BRIDGE + "/lists");
    lists = await r.json();
  } catch (e) {
    say(NO_BRIDGE, "err");
    return;
  }

  fill($("model"), lists.models || [], "— из config_ps.txt —", true);
  fill($("vae"), lists.vaes || [], "— из модели —", true);
  fill($("lora"), lists.loras || [], "нет лоры", true);
  fill($("embedding"), lists.embeddings || [], "нет", false);

  // по умолчанию — то, что стоит в config_ps.txt
  const byBase = (arr, name) => (arr || []).find(
    (x) => x.replace(/\.(safetensors|ckpt|pt)$/i, "") === name) || "";
  pick($("model"), byBase(lists.models, lists.model));
  pick($("vae"), byBase(lists.vaes, lists.vae));
  pick($("lora"), byBase(lists.loras, lists.lora));
  if (lists.lora_weight) setVal("loraWeight", lists.lora_weight);
  if (lists.steps) setVal("steps", lists.steps);
  if (lists.cfg) setVal("cfg", lists.cfg);

  // ...а поверх — снова то, что ты выбирал в прошлый раз: списки приехали
  // только сейчас, до них выбрать в них было нечего
  applySaved();

  const ping = await fetch(BRIDGE + "/ping").then((r) => r.json()).catch(() => null);
  if (ping && !ping.comfy) {
    say("Мост есть, а ComfyUI не запущен.\nЗапусти ComfyUI и открой панель заново.", "err");
  } else if (ping && ping.missing && ping.missing.length) {
    // без этих нод граф не соберётся — лучше сказать сразу, чем ронять генерацию
    say("В ComfyUI не хватает нод:\n" + ping.missing.join("\n") +
        "\nПоставь их через ComfyUI Manager и перезапусти ComfyUI.", "err");
  } else {
    say("Мост на связи. Выдели область и жми.", "ok");
  }
}

$("go").addEventListener("click", generate);

function showBlend() {
  const v = parseInt(getVal("blend"), 10) || 0;
  $("blendLabel").textContent = v === 0
    ? "Растушёвка края: 0 px — жёсткий край по выделению"
    : `Растушёвка края: ${v} px — затухание наружу`;
}
$("blend").addEventListener("input", showBlend);
$("blend").addEventListener("change", showBlend);
showBlend();

init();
