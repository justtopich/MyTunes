import os
import shutil
from pathlib import Path


PACKAGE = "MyTunes"


def install():
    try:
        with open(f'myTunes/__init__.py', 'r') as file:
            for line in file.readlines():
                if line.startswith("__version__"):
                    line = line.strip().replace("'", '"', -1)
                    version = line[line.find('"') + 1:-1]
                    break
    except Exception as e:
        input("can't read myTunes/_init__.py: %s" % e)
        return

    lines = []
    try:
        with open('version.txt', 'r') as file:
            for line in file.readlines():
                if "fileversion" in line.lower():
                    lines.append(f"{line[:line.find('build') + 5]}{version.split('.')[-1]}'),\n")
                elif "productversion" in line.lower():
                    lines.append(f"{line[:line.find(', u') + 4]}{version}')])\n")
                else:
                    lines.append(line)
    except Exception as e:
        input("can't read version.txt: %s" % e)
        return

    try:
        with open('version.txt', 'w') as file:
            file.writelines(lines)
    except Exception as e:
        input("can't write version.txt: %s" % e)
        return

    try:
        os.system(f"pyinstaller --clean --workpath myTunes --distpath bin {PACKAGE}.spec")
    except Exception as e:
        input("can't call pyinstaller: %s" % e)

    shutil.rmtree('myTunes/MyTunes')