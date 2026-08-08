# Заготовка для EXE. Специально тупая: она умеет ровно одно — позвать
# python_embeded\python.exe запустить launcher.py, который лежит рядом.
#
# Почему так. EXE — слипшийся кусок на несколько мегабайт, его нельзя
# поправить одной строчкой и нельзя дёшево обновить: каждая пересборка
# ложится в историю целиком. А ещё Windows держит запущенный EXE и не
# даёт переписать его самого.
#
# Поэтому вся начинка живёт в launcher.py — обычном текстовом файле.
# Его патч меняет килобайтами, и в момент обновления его никто не держит.
# Этот же EXE собирается один раз и меняться ему незачем.
import os, sys, subprocess

if getattr(sys, "frozen", False):
    HERE = os.path.dirname(os.path.abspath(sys.executable))
else:
    HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PY = os.path.join(HERE, "python_embeded", "python.exe")
LAUNCHER = os.path.join(HERE, "launcher.py")


def стоп(текст):
    print(текст)
    print()
    input("Нажми Enter, чтобы закрыть окно.")
    sys.exit(1)


if not os.path.exists(PY):
    стоп("Не нашёл python_embeded\\python.exe рядом с этим файлом.\n"
         "Похоже, EXE вынесли из папки сборки — верни его обратно.")

if not os.path.exists(LAUNCHER):
    стоп("Не нашёл launcher.py рядом с этим файлом.\n"
         "Похоже, EXE вынесли из папки сборки — верни его обратно.")

sys.exit(subprocess.call([PY, "-s", LAUNCHER] + sys.argv[1:], cwd=HERE))
