from kulms_download.constants import *
import pickle
import platform
import subprocess
import os
from pathlib import Path
from kulms_download.settings import shared_settings
from kulms_download.kulms_components import *

def get_pickle() -> Site:
    f = open("output/prob_and_statis.pickle", "rb")
    return pickle.load(f)

def show_tree_structure(root: Content):
    if root is None:
        return ""

    lines = [str(root.title)]

    def recursive(node: Content, prefix: str):
        child_count = len(node.children)
        for i, child in enumerate(node.children):
            is_last = i == child_count - 1
            branch = "`-- " if is_last else "|-- "
            lines.append(f"{prefix}{branch}{child.title}")
            next_prefix = f"{prefix}{'    ' if is_last else '|   '}"
            recursive(child, next_prefix)

    recursive(root, "")
    tree_text = "\n".join(lines)
    print(tree_text)


def open_app_from_path():
    if not shared_settings.password_app_executable_path:
        return
    
    path = Path(shared_settings.password_app_executable_path)
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")

    current_os = platform.system()

    if current_os == "Windows":
        os.startfile(path)
        
    elif current_os == "Darwin":  # macOS
        subprocess.run(["open", str(path)], check=True)
        
    else:  # Linux (Ubuntu等)
        subprocess.run(["xdg-open", str(path)], check=True)