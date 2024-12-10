from os import name, path as px
from json import load


def load_conf(path=None):
    if not path:
        path = px.join(px.dirname(__file__), "config.json")
    with open(path, "r", encoding="utf-8") as cf:
        return load(cf)

cfg = load_conf()

def isWindows():
    return name == 'nt'

img_debug = False