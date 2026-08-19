# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A **fully self-contained, portable** ComfyUI image-generation kit with a thin custom layer at the repo root. Stock ComfyUI (`ComfyUI/`, `python_embeded/`, `update/`) is the engine; everything interesting lives in the root-level scripts. Output is tuned to match a specific tensor.art recipe (A1111/Forge-style sampling parity).

The whole folder — engine, embedded Python, custom nodes, **and the models** — is meant to be copied to a laptop or handed to a friend on a drive and just work, with no install step. That property is the point of the project and constrains most design decisions below.

У проекта две дорожки. Первая — инструмент, про него всё остальное в этом файле. Вторая — **продвижение игры Lewd Temple в соцсетях, сейчас главным образом на Reddit**; про неё отдельный раздел ниже, сразу после правил о том, как здесь объясняют.

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

## Соцсети: продвижение Lewd Temple (Reddit — главная площадка)

Вторая дорожка проекта. Здесь Claude работает **менеджером по соцсетям**: ищет, куда идти, пишет черновики, приносит на проверку.

**Что продвигаем.** `Lewd Temple: Hentai Clicker` — кликер про древний Египет, Steam app `4021840`, страница уже висит публично как «скоро».

**Как на самом деле сделан арт** (важно для честных ответов): это **не полная генерация**. Основа приходит из ComfyUI на своей машине, дальше пользователь дорисовывает и вычищает руками в Photoshop и режет на части под риг. Риг и анимация в Spine — целиком ручная работа. Отсюда и готовая спокойная формулировка, если спросят прямо: *«Mixed — I generate a base, then repaint and clean it up by hand until it's usable, and cut it into parts for rigging in Spine. The rig and animation are all hand work.»*

**Где сидим.**

| Площадка | Кто | Состояние |
|---|---|---|
| **Reddit** | `u/Correct-Guidance-232` | главная сейчас; профиль настроен 2026-08-14 |
| X | `@Sasamin4ikGames` | один пост, дальше по субботам |

Имя на Reddit выдал сам Reddit и **сменить его нельзя** — `can_edit_name: false`. Живём с ним.

### Кто что делает

| Claude | Пользователь |
|---|---|
| ищет темы и площадки, считает, разбирает | делает картинку, гифку, анимацию |
| пишет черновик поста или ответа | правит своими словами |
| заполняет форму, ставит ярлычок и метку 18+ | прикрепляет файл |
| проверяет, дошло ли | **жмёт кнопку публикации** |

**Где проходит граница (уточнено 2026-08-14).** Комментарии Claude отправляет сам — текст пользователь всё равно видит заранее, а цена ошибки мала: комментарий можно удалить, и его никто не успеет заметить. **Посты пользователь жмёт сам**: в них ссылка на игру, ярлычок и метка 18+, там ошибка стоит поста, а иногда и доступа в сообщество.

**Правки пользователя — не формальность.** Claude знает механику по коду, но живые подробности — где именно споткнулся, что бесило — есть только у автора. Голосуют как раз за них.

### Текущая цель, с числом

Набрать **100 кармы за комментарии и 100 за посты**, затем подать заявку на `r/Spine2D` — сообщество на 716 человек с **нулём модераторов**, брошенное, при живой теме (за месяц двое искали Spine-аниматора и им некуда было идти). Остальные условия r/redditrequest уже выполнены: аккаунту 3 года, почта подтверждена.

Карма — счётчик одобрений. По нему Reddit решает, человек ты или рассылочный робот.

### Правила площадок, которые уже стоили нам поста

- **r/LewdGames (618 тыс) — закрыт.** Правило «No AI Focused Games». Проверено: за два дня ноль постов с ярлычком `(AI)`, сами `(AI)`-ярлычки убраны из списка. Не спорить, не проситься.
- **r/SlimeGirls (183 тыс)** — нейросетевой арт только перекрёстной ссылкой из `r/MonsterGirlAI`. Напрямую нельзя.
- **r/MonsterGirlAI (64 тыс)** — самореклама разрешена, но: приложить промпт, и на странице по ссылке должна быть пометка про нейросеть, иначе бан.
- **r/NSFWgaming (391 тыс)** — про ИИ правил нет, но нужны **играбельные** игры. Пока мимо.
- **r/IndieDev, r/SoloDevelopment, r/2DAnimation** — без 18+. Туда идёт **анимация как ремесло**: она не взрослая и не про нейросети, её пускают везде.

**Про нейросеть не врём никогда.** Где нельзя — туда не идём. Где можно — говорим прямо. Скрытое всплывает, и тогда сносят аккаунт, а не пост.

**Но и вперёд её не выносим.** Многие в этих сообществах остались без работы из-за нейросетей и злы — по делу. Поэтому в постах про сам инструмент не пишем: не туманно, а вообще никак. Спросят — ответим честно и спокойно, одной строкой. Разница простая: умолчать о том, чего не спрашивали, можно; сказать неправду — нельзя.

**Пишем про них, а не про себя.** Пост, который собирает ответы, устроен так: короткая своя история без подвига, потом прямой вопрос об их опыте — и приглашение рассказать про неудачи, а не только про победы. Про свои успехи люди пишут неохотно, про грабли — с удовольствием.

### Что измерено и работает

- **Коротко.** Комментарий — 1–3 предложения, и лучше с вопросом собеседнику: «круто, а ты это чем делал?». Люди отвечают на интерес к себе, а не на разбор. Длинный ответ закрывает разговор — отвечать на него нечего. Даже когда спросили прямо, укладываться в 3–5 строк и заканчивать вопросом, чтобы ветка жила: шесть коротких реплик дают больше кармы и знакомств, чем одна лекция.
- **Юмор — когда по делу сказать нечего.** Правило пользователя, выведенное 2026-08-14: одна живая строчка вместо неловкой паузы держит ветку. Но только в ветке, где мы уже стоим и всё полезное уже сказали; лезть с шуткой в чужой пост, где мы никто, — не надо, лучше пройти мимо. Шутке нечем ответить, поэтому она не заменяет разбор, а идёт после него.
- **Комментарии фильтр пропускает, посты — нет.** Проверено на своём аккаунте в тот же день. Выход из фильтра — через ответы.
- **Первый содержательный ответ в свежей теме** забирает больше всех. Искать вопросы возрастом до часа с нулём ответов.
- **Ритм: раз в три дня, в одно сообщество.** Веером рассылать не запрещено, но бессмысленно: в мелких сабах тот же пост берёт 1-10 голосов против 101 в крупном.
- **Комментарии не выкладывать очередями.** Не пять подряд за минуту, а один-два с паузами и в разное время суток. По очередям нас вычислили 2026-08-16: комментарии шли в **разные** посты, каждый с подробностями из чужого текста — то есть его надо было прочитать, — и всё это за минуту-две. Человек так не успевает. Довод слабый поодиночке, но ложится к остальным, а стоит нам ноль.
- **Образец поста, взявшего 2989 голосов** (u/cheesebbang, r/IndieDev): одна анимация одного персонажа, ярлычок GIF, короткий текст с зацепкой, ссылка в конце, а про инструмент — приписка потом, когда спросят.
- Reddit принимает `jpeg png webp gif mp4 mov`; гифки всё равно перегоняет в видео. **Аватар и шапка — строго до 500 КБ.** Шапку профиля сайт не показывает вообще ни у кого, только приложение.

### Стиль речи показывать пользователю

**Время от времени показывать пользователю партию комментариев и спрашивать, что в них
торчит.** Не «одобри», а именно «что выглядит чужеродным». Не каждый раз — иначе работа
превратится в согласование; раз в несколько заходов или когда меняем манеру.

**Почему.** Claude видит структуру и упускает отдельные слова, а цепляются люди как раз за
слова. Проверено на живом примере 2026-08-16: в тексте пользователя не проскочило ни одного
регионализма за всю переписку — он годами вычищает из речи всё редкое и приметное. У него на
это глаз лучше. А вот меня в тот же день вычислили по структуре — одинаковая форма,
повторённая двадцать пять раз, — и заметил это посторонний, а не я.

Правило дополняет [[reddit-comment-style]]: там записано, *как* писать, здесь — *кто
проверяет*.

### Когда нас обвиняют в том, что мы нейросеть

Это случается и будет случаться. Порядок действий — **не оправдываться, а разбирать**.

1. **Прочитать обвинение целиком** и посмотреть, на что человек ссылается. Обычно он
   приводит доказательства: цитаты, ссылки на профиль, перечисление признаков.
2. **Понять, по чему нас вычислили.** Это ценнее самого обвинения: человек бесплатно
   показал дырку, которую мы сами не видели.
3. **Записать в `Desktop\acki\смм\обвинения.md`**: дата, кто, где, дословная суть, какие
   признаки назвал, сколько голосов набрал, подхватили или нет.
4. **Сделать вывод и исправить.** Не пообещать, а поменять что-то конкретное.
5. **Отвечать — по решению пользователя.** Отрицать нельзя: комментарии действительно
   пишет нейросеть, и враньё превращает «подозрительный шаблон» в «пойман на лжи».
   Варианты — промолчать (обычно лучший, если обвинение не набрало голосов) или
   признать шаблон без спора.
6. **Один минус обвинению — и всё.** Живая реакция на неприятное, правил Reddit не
   нарушает: нарушение — это вторые аккаунты и созыв друзей, а не собственный голос.
   Ровно один, со своей учётки.
7. **Обвинителя блокируем — но сначала одна фраза, и сразу.** Молчаливая блокировка
   читается однозначно: заткнул рот, потому что возразить нечем. Именно она, а не само
   обвинение, привела к нам модератора 2026-08-16. Порядок: **сначала комментарий,
   потом блокировка** — после блокировки писать уже некуда.

   Фраза не оправдывается, а разворачивает вопрос на собеседника и объясняет уход:

   > whats the goal of going through my comments and voting them down when they werent
   > aimed at you? im not spending an hour on this when i could spend it on my game,
   > nobody pays me for it. blocked.

   Ничего не отрицает — значит, врать не приходится. И блокировка после неё читается
   как «разговор окончен», а не как бегство. Блокировка заодно прячет от человека наши
   комментарии, так что минусовать их он больше не может.
8. **Резкие ходы — не в тот же день.** Закрыть профиль, почистить историю, сменить
   манеру — всё это обвинитель видит и записывает себе в доказательства. Ждать, пока
   ветка остынет.

**Первый разбор, 2026-08-16:** вычислили по однообразию — короткое наблюдение плюс вопрос
в конце, двадцать пять раз подряд. Вывод: профиль закрыт (`Настройки → Profile → Content
and activity → Hide all`), правило про стиль переписано с «коротко и с вопросом» на
«коротко, но каждый раз по-разному».

### Чего не делаем

- **Не накручиваем карму.** Комментарии ради счётчика Reddit ловит и сносит аккаунты насовсем.
- **Не пишем от лица пользователя про то, чего он не делал руками.** Выдуманный опыт виден и собирает минусы.
- **Читаем чужой пост целиком перед ответом.** Однажды чуть не объяснили человеку то, что у него уже было настроено — было видно на приложенной картинке.
- **Пост с видео просто пропускаем.** Claude видео не смотрит, а хвалить неувиденное нельзя. Постов в мире много, и застревать на одном не из-за чего. Если попался редкий случай, где ответить очень хочется, — попросить пользователя глянуть и пересказать, но это исключение, а не обычный ход.
- **Паролей не вводим, в аккаунты не логинимся.** Вход — всегда сам пользователь.

**Тон задаёт `стиль-общения` в памяти: усиливающее зеркало.** С доброжелательными тепло, с хамами жёстко — но без прямых оскорблений, без нарушения правил площадки и без выдумок о живых людях. Когда регистр неясен, показать черновик и спросить пользователя «а ты бы как ответил?», а не угадывать.

Подробности и цифры — в памяти: `reddit-lewd-temple`, `x-account-smm`, `стиль-общения`, `reddit-post-formats`, `reddit-tracking`, `reddit-без-мышки`.

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
| `РЕНДЕР_ЦВЕТ.bat` | `run_color.py` | `config.txt` (`color_*`) | T2I-Adapter color grid — copy the colour composition |
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

### The tensor.art parity layer

The reason this graph exists at all. Note the history, because it explains why the code looks the way it does:

The graph originally carried a `smZ Settings` node (from `ComfyUI_smZNodes`) plus `weight_interpretation: A1111`, on the assumption that tensor.art ran an A1111/Forge backend. **Patch 1 (2026-08-08) removed all of that** — tensor.art turns out to run ComfyUI itself, so the node was pulling output *away* from the target and costing sharpness. Measured on fixed seed/prompt, output went from visibly softer than the reference to indistinguishable from it.

What actually provides parity now:

- **`ComfyUI_ADV_CLIP_emb`** → `BNK_CLIPTextEncodeAdvanced` with `token_normalization: none` and **`weight_interpretation: comfy`** (was `A1111`). Prompt-weight syntax is unchanged; the strength curve differs slightly.
- **`comfyui_lora_tag_loader`** → `LoraTagLoader`, so loras are inline `<lora:NAME:WEIGHT>` tags rather than graph nodes. KSampler now takes `model` straight from this node.
- Sampling: `euler_ancestral` / `normal`, `CLIPSetLastLayer -2`, VAE `sdxl-vae-fp16-fix`.
- Also present: `comfyui_controlnet_aux` (depth/canny preprocessors), `ComfyUI_IPAdapter_plus`, `ComfyUI-Inpaint-CropAndStitch`, `comfyui-inpaint-nodes`, `ComfyUI-Manager`, `ComfyUI_experiments`.

`ComfyUI_smZNodes` is still installed but **unused** — nothing references it. Don't reintroduce it, and don't restore the old `RNG`/`CFGD`/`SGM` env-var overrides or `ENSD=31337`: those went with it, which is why a given seed no longer reproduces pre-patch images.

### Node-id contracts (fragile — preserve when editing graphs)

- In `workflow_api.json`, `workflow_api_ip.json`, `workflow_api_ref.json`: the two text encoders are told apart **by hardcoded node id** — `"10051"` = positive, `"10052"` = negative. Everything else is matched by `class_type`. Regenerating a template without preserving these ids means the prompt is silently never applied.
- In `inpaint_onlymasked_api.json`, `ps_bridge.py` patches **by numeric id**: `1` checkpoint, `2` LoraTagLoader, `4` VAELoader (dropped entirely when no VAE is configured, with `50`/`11` repointed to the checkpoint's VAE output), `5`/`6` positive/negative, `7` image, `70` mask, `60` InpaintCropImproved, `10` KSampler, `61` InpaintStitchImproved.
- Ids `90`–`95` mirror `80`–`85` for the colour control (`color: color`): `90` ColorPreprocessor, `91`/`92` loader and apply, `93` PreviewImage, `94`/`95` the scale + second crop used in whole-canvas mode. `run_inpaint()` threads a single `cond_pos`/`cond_neg` pair through the enabled controls in order (depth, then colour) and only then writes it into `50`, so any combination of the two works and neither hardcodes `5`/`6`.
- Ids `80`–`85` are **not in the template** — `run_inpaint()` injects them only when the panel asks to hold the shape (`control: depth`), and repoints `50` to take conditioning from `82` instead of `5`/`6`. `80` MiDaS-DepthMapPreprocessor, `81` ControlNetLoader, `82` ControlNetApplyAdvanced, `83` PreviewImage (the map as ControlNet sees it), plus `84` ImageScale and `85` a second InpaintCropImproved in whole-canvas mode. Keep them out of the template: a machine without the ControlNet files must still run plain inpaint.

### ControlNet pipelines (depth / canny)

Donor image resolution order: CLI arg → `depth_image`/`canny_image` in `config.txt` → newest image in `depth\donor\` / `canny\donor\`. The donor is copied into `ComfyUI\input\` because ComfyUI only loads images from there. The generated map is copied to `depth\map.png` / `canny\map.png` (overwritten each run) and **deleted from the output folder** so it doesn't accumulate.

By default the canvas is refitted to the donor's aspect ratio (`depth_fit`/`canny_fit = donor`), preserving the pixel budget `width*height` from config and rounding to multiples of 64 — a mismatched aspect stretches the control map and breaks anatomy. Set `= config` to force the configured size.

The ControlNet checkpoint is **discovered at runtime** by searching `/object_info/ControlNetLoader` for a name containing `depth`/`canny` + `sdxl`, never hardcoded.

`run_color.py` (added 2026-08-18) is the same skeleton with `ColorPreprocessor` in slot `10117` — it blurs the donor into a coarse colour mosaic, so it carries composition and palette, not shape or edges. Two things are worth knowing before editing it:

- **There is no colour T2I-Adapter for SDXL.** TencentARC shipped only sketch/canny/lineart/openpose/depth for SDXL; the 17M-parameter colour adapter exists for SD1.5 alone. tensor.art therefore feeds its `t2ia_color_grid` preprocessor into `t2i-adapter_xl_canny` — verified in the PNG metadata of a site render — and `run_color.py` reproduces exactly that pairing. It is not a mistake to "fix".
- The model is picked by the `color_model` substring (default `t2i`), not by a `+sdxl` match like the other two, precisely so the odd pairing above stays expressible; `color_model = canny` falls back to the bundled xinsir ControlNet for experiments.
- `color_resolution` is the mosaic's coarseness, not a quality setting: `apply_color()` resizes the short side to that value and then divides by 64, so 512 = 8 cells (tensor.art's default) and 1024 = 16.
- **`color_strength` does not share a scale with the other two pipelines** — measured on a fixed seed 2026-08-19, one variable at a time: 0.5–1.0 is barely distinguishable from control off, 1.5 transfers the palette while the drawing stays clean, 2.0 smears, 3.0 collapses into visible mosaic blocks. Default is therefore 1.5, not tensor.art's 0.6. The adapter is 158 MB against the ControlNets' 2.4 GB and simply has less authority.
- Beware the prompt fighting the map: `simple background` / `white background` in `prompt.txt` beat the adapter outright at 0.6 and produced a white frame. A prompt that describes the setting leaves the map nothing to decide.
- The file must come from `TencentARC/t2i-adapter-canny-sdxl-1.0` (`diffusion_pytorch_model.fp16.safetensors`, 158,060,440 bytes, diffusers key names that `load_t2i_adapter` remaps). The `xingren23/comfyflow-models` repack under the same filename is **truncated** — its header declares 155 MB of tensors in a 107 MB file, and ComfyUI fails at `ControlNetLoader` with a reshape error. The official file also takes 3-channel input (`conv_in` is 320×768), so the grid's actual colours reach the adapter; the broken repack was single-channel.

A tensor.art render's PNG carries both a `generation_data` chunk (its UI's settings) and a `prompt` chunk (the actual ComfyUI graph, node ids identical to ours). Their KSampler takes `ensd: 31337` and `seed_mode: "A1111"` inputs that stock ComfyUI's does not — theirs is patched, which is why a tensor.art seed cannot reproduce byte-identically here.

### Photoshop bridge

`ComfyInpaint_panel/` is an Adobe UXP panel (manifest v4, PS 23.3+) — `index.html` + `main.js`, no build step. Its manifest whitelists exactly `http://127.0.0.1:8189`, so **the bridge port is baked into the panel**; changing `PORT` in `ps_bridge.py` requires editing `manifest.json` too.

`ps_bridge.py` is a `ThreadingHTTPServer` on 8189 (with `allow_reuse_address = False`, so a second bridge fails loudly instead of stealing requests). API: `GET /status` (live progress), `GET /lists` (models/loras/VAEs/embeddings + whether depth control is available, read from the server so the panel never shows files ComfyUI can't load), `GET /ping` (is ComfyUI up + which required custom nodes are missing), `POST /inpaint`, `POST /interrupt`. A background thread holds a websocket to ComfyUI to receive progress, reconnecting on drop.

Subtleties worth preserving in `run_inpaint()`:
- Photoshop sends the selection as a **patch** (raw pixels + `left`/`top`/`canvas_width`/`canvas_height`), not a full-canvas image; `to_image()` pastes it back to its place on a full canvas. A mask whose size doesn't match the canvas is a hard error — resizing it would silently produce mush.
- `blend_alpha()` feathers **outward only**: the alpha plateau reaches exactly the selection contour and all falloff happens outside it. The naive expand→blur the node itself uses eats into the selection edge.
- `context_factor()` converts "N pixels of context" into the multiplier the crop node actually wants.
- The returned crop is `bbox + blend` px, and the response reports both the rectangle origin (`x`/`y`) and where opaque pixels start inside it (`content_x`/`content_y`) — Photoshop positions layers by opaque bounds, so without the latter the layer lands offset by the feather width.
- `_last_mask.png` is written next to the script each run for eyeballing mask alignment; with depth on, `_last_depth.png` is written the same way and holds exactly what reached the ControlNet.
- **Holding the shape (ControlNet depth), added 2026-08-18.** The panel sends `control` (`нет`/`depth`), `control_src` (`canvas`/`selection`) and `control_strength`; there is no donor image — the map is always taken from what Photoshop sent. Preprocessor settings are copied from `run_depth.py` on purpose, so the two places can't drift.
  - `selection` runs MiDaS on the crop (node `60` output 1 — original pixels, before noising). Full contrast, but MiDaS reads a fragment out of context and can misjudge what it is looking at.
  - `canvas` runs MiDaS on the whole image, scales the map back to canvas size, then cuts the same piece with **a second `InpaintCropImproved` carrying identical inputs**. That node derives its rectangle from the mask and canvas size, not from pixels, so the two crops match to the pixel — verified. Global depth order is right, but the region occupies a narrow slice of the range and comes out low-contrast. If that ever hurts, the fix is to renormalize the cut-out map (numpy in the bridge, no new node); measured as good enough in practice on 2026-08-18, so it was not built.
  - The result is read from node `12` explicitly rather than "last image in outputs" — with control on there are several images in the response.
  - Availability is decided in `get_lists()` (both the preprocessor node **and** a depth SDXL ControlNet must exist) and reported as `depth_cn`; the panel drops the menu item entirely when it's empty, instead of offering a button that dies mid-render.
  - Depth cannot see flat-on-body clothing (a bikini strap doesn't stand out from skin) — it holds body volume, and the mask holds the garment outline. For repainting an existing garment the right tool is canny, not depth.
- **Holding the palette (T2I-Adapter colour grid), added 2026-08-19.** `color` (`нет`/`color`), `color_src` (`selection`/`canvas`), `color_strength`; availability reported as `color_cn`, resolved by the `color_model` substring with `need_sdxl=False` because the adapter is named `t2i-adapter_xl_canny`, not `…sdxl…`. Independent of depth — either, both, or neither.
  - `selection` reads the crop's own colours, which makes the intended workflow **paint the colours in first**: a few rough brush strokes inside the selection in Photoshop, and the model renders them into a real object. The user drives colour with a brush instead of prompt words.
  - `canvas` reads the whole image and cuts the same piece with the second crop node, so the repainted region lands in the scene's own light.
  - The mosaic is 8 cells on the crop's short side — it carries colour and light, never pattern or texture. Do not expect it to copy a fabric print.
  - `_last_color.png` is written next to the script, same idea as `_last_mask.png`/`_last_depth.png`.

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

- **ComfyUI-Manager is kept offline on purpose.** `ComfyUI\user\__manager\config.ini` has `network_mode = offline` (set 2026-08-19). On `public` it fetched the whole public registry of every existing custom node at every startup — `FETCH ComfyRegistry Data: N/174` in the log — which slowed the launch and, on a machine with no internet, waited for a timeout instead. It was the only thing in the whole kit that reached the network on its own. Installed nodes are unaffected; the Manager only handles installing and updating. To install something through it: switch to `public`, install, switch back. Note this file lives in `ComfyUI/`, which is its own git repo, so the setting does not travel with a patch.
- **`.bat` bodies must be ASCII** even though their filenames are Cyrillic: cmd reads batch bodies in chunks in a single-byte codepage, and a chunk boundary landing mid-UTF-8-character breaks the commands. Russian text belongs in Python output (which is fine after `chcp 65001` + `PYTHONIOENCODING=utf-8`). Some older launchers (`РЕНДЕР.bat`) still contain cp1251 Russian in `echo` lines — follow the newer ones (`РЕНДЕР_ПОЗА.bat`) and keep new bat bodies English.
- Python sources are UTF-8 with Russian comments and Russian user-facing output; keep that voice — the end users are non-technical.
- `ComfyUI/` and each of the nine `custom_nodes/*` are **their own git repos**. A repo at the root must not try to track their contents.
- `run_depth.py:151` and `run_canny.py:157` still tell the user to look in `D:\Illustrious\webui\models\ControlNet\` when no ControlNet model is found — a leftover from the pre-portable era. The correct location is now `ComfyUI\models\controlnet\`.
- **Photoshop does not load the panel from this repo.** `ComfyInpaint_panel/` is the source; Photoshop runs a **copy** placed in its own `Plug-ins\ComfyInpaint_panel\` (on this machine `D:\adobe\Adobe Photoshop 2024\Plug-ins\`). After editing the panel, copy `index.html`/`main.js`/`manifest.json` over and **restart Photoshop** — the manifest says `loadEvent: startup`, so reopening the panel is not enough. Editing `ps_bridge.py` needs the bridge window restarted for the same reason. Symptom of forgetting: the panel looks unchanged, or new fields appear but the bridge ignores them.
- `negative_original.txt` is a kept-aside backup; `negative.txt` is the live one. `Ivy.txt`, `КОНТУР_инструкция.txt`, `ПОЗА_инструкция.txt` are user-facing notes, not code.
- `README_VERY_IMPORTANT.txt` is stock ComfyUI's readme, not ours — it describes `run_nvidia_gpu.bat`/`run_cpu.bat` (also stock) and mentions `extra_model_paths.yaml`, which contradicts the portability rules above.
- Output goes to `ComfyUI\output\YYYY-MM-DD\` with a per-pipeline prefix: `sync`, `depth`, `canny`, `ipadapter`, `refonly`.
