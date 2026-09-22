import os
import shutil
import zipfile

root = r"C:\Users\shreya\discord-fly-brain"
out = os.path.join(root, "fly-deploy-clean.zip")
tmp = os.path.join(root, ".ziptmp_clean")

if os.path.exists(tmp):
    shutil.rmtree(tmp)
os.makedirs(tmp, exist_ok=True)

include = [
    "brain_dashboard.py",
    "dashboard_animation.py",
    "experiment_runner.py",
    "fly_bot.py",
    "fly_controller.py",
    "group_brain.py",
    "memory.py",
    "social_simulation.py",
    "group_weights.json",
    "fly_state.json",
    "requirements.txt",
    "dashboard assests",
    "sprites",
]

for item in include:
    src = os.path.join(root, item)
    dst = os.path.join(tmp, item)
    if os.path.isdir(src):
        shutil.copytree(src, dst, dirs_exist_ok=True)
    elif os.path.isfile(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)

with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for dirpath, dirnames, filenames in os.walk(tmp):
        dirnames[:] = [d for d in dirnames if d not in {".git", ".venv", ".pytest_cache", "__pycache__"}]
        for filename in filenames:
            if filename in {".env"} or filename.endswith(".pyc"):
                continue
            full = os.path.join(dirpath, filename)
            arc = os.path.relpath(full, tmp)
            z.write(full, arc)

shutil.rmtree(tmp, ignore_errors=True)
print(out)
