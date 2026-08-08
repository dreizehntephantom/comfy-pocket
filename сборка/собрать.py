# Собирает ЗАПУСК.exe — ту самую кнопку с зелёной плиткой.
#
# Запуск:  python_embeded\python.exe сборка\собрать.py
#
# Делать это надо РЕДКО. EXE ничего не знает и не меняется: вся начинка
# в launcher.py. Пересобирать нужно, только если поменялась заготовка
# exe_stub.py или иконка.
#
# Собиралка (PyInstaller) весит около 30 МБ и качается сюда же, в папку
# _pyinstaller. В историю проекта она не едет — стоит в списке исключений.
import os, sys, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = os.path.join(ROOT, "python_embeded", "python.exe")
TOOLS = os.path.join(HERE, "_pyinstaller")
ICON = os.path.join(HERE, "icon.ico")
STUB = os.path.join(HERE, "exe_stub.py")
OUT_NAME = "comfy-pocket"                      # собираем под латинским именем
FINAL = os.path.join(ROOT, "ЗАПУСК.exe")       # кладём под русским


def шаг(s):
    print("\n=== " + s, flush=True)


шаг("проверяю собиралку")
if not os.path.isdir(os.path.join(TOOLS, "PyInstaller")):
    print("не нашёл, качаю (это разово, около 30 МБ)...")
    subprocess.check_call([PY, "-m", "pip", "install", "--target", TOOLS,
                           "pyinstaller", "--quiet", "--disable-pip-version-check"])
print("собиралка на месте:", TOOLS)

шаг("собираю EXE")
# У встроенного Python есть файл-ограничитель путей, из-за него переменная
# PYTHONPATH не работает. Поэтому путь к собиралке подсовываем прямо в коде.
код = (
    "import sys, os\n"
    f"sys.path.insert(0, r'{TOOLS}')\n"
    "import PyInstaller.__main__\n"
    "PyInstaller.__main__.run([\n"
    "    '--onefile', '--console', '--noconfirm',\n"
    f"    '--icon', r'{ICON}',\n"
    f"    '--distpath', r'{os.path.join(HERE, '_dist')}',\n"
    f"    '--workpath', r'{os.path.join(HERE, '_work')}',\n"
    f"    '--specpath', r'{HERE}',\n"
    f"    '--name', '{OUT_NAME}',\n"
    f"    r'{STUB}',\n"
    "])\n"
)
subprocess.check_call([PY, "-c", код])

шаг("кладу на место")
собранный = os.path.join(HERE, "_dist", OUT_NAME + ".exe")
if not os.path.exists(собранный):
    sys.exit("EXE не собрался — смотри, что написано выше.")
shutil.copy2(собранный, FINAL)
print("готово:", FINAL)
print("вес: %.1f МБ" % (os.path.getsize(FINAL) / 1024 / 1024))
print("\nПроверь: щёлкни по ЗАПУСК.exe в главной папке.")
