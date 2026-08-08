# Собирает обновление и вписывает его в список на сайте.
#
# Запуск из главной папки:
#   .\python_embeded\python.exe сборка\собрать_патч.py <папка> <номер> "<название>"
#
# Пример:
#   .\python_embeded\python.exe сборка\собрать_патч.py D:\1\ComfyUI_portable_ПАТЧ 1 "картинки стали чётче"
#
# Что делает: складывает всё из папки в patches\patch-NNN.zip, считает
# отпечаток и дописывает строчку в patches\index.json.
#
# Файлы в папке должны лежать так, как они лягут в главную папку сборки.
# ЧТО_ДЕЛАТЬ.txt — рассказ для человека, он показывается и на диск не кладётся.
import os, sys, json, hashlib, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PATCHES = os.path.join(ROOT, "patches")
INDEX = os.path.join(PATCHES, "index.json")

if len(sys.argv) < 4:
    sys.exit(__doc__ or "Нужно: <папка> <номер> <название>")

SRC = os.path.abspath(sys.argv[1])
N = int(sys.argv[2])
TITLE = sys.argv[3]

if not os.path.isdir(SRC):
    sys.exit(f"Нет такой папки: {SRC}")

os.makedirs(PATCHES, exist_ok=True)
name = f"patch-{N:03d}.zip"
zpath = os.path.join(PATCHES, name)

# --- складываем ---
файлы = []
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    for dirpath, _, names in os.walk(SRC):
        for fn in sorted(names):
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, SRC).replace(os.sep, "/")
            z.write(full, rel)
            файлы.append(rel)

blob = open(zpath, "rb").read()
отпечаток = hashlib.sha256(blob).hexdigest()

print(f"Собрано: patches\\{name}  ({len(blob)//1024} КБ)")
for f in файлы:
    метка = "  (показывается, не кладётся)" if f == "ЧТО_ДЕЛАТЬ.txt" else ""
    print(f"   {f}{метка}")

# --- вписываем в список ---
данные = {"patches": []}
if os.path.exists(INDEX):
    данные = json.load(open(INDEX, encoding="utf-8"))

данные["patches"] = [p for p in данные.get("patches", []) if int(p["n"]) != N]
данные["patches"].append({"n": N, "file": name, "sha256": отпечаток, "title": TITLE})
данные["patches"].sort(key=lambda p: int(p["n"]))

with open(INDEX, "w", encoding="utf-8") as f:
    json.dump(данные, f, ensure_ascii=False, indent=2)
    f.write("\n")

print(f"\nВписано в patches\\index.json под номером {N}: {TITLE}")
print("Теперь отправь всё на GitHub — и сборки начнут это видеть.")
