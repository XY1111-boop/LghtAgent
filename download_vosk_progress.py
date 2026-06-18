# download_vosk_progress.py —— 带实时进度条，多源自动切换
import os, sys, urllib.request, zipfile, time

MODEL_DIR = r"E:\LightAgent\models"

# 稳定镜像源（GitHub 官方 + 国内镜像）
URLS = [
]

def show_progress(block_num, block_size, total_size):
    downloaded = block_num * block_size
    percent = min(100, int(downloaded * 100 / total_size)) if total_size > 0 else 0
    sys.stdout.write(f"\r  下载进度: {percent}% ({downloaded}/{total_size})  ")
    sys.stdout.flush()

def try_download(url):
    try:
        print(f"⬇️ 尝试: {url}")
        urllib.request.urlretrieve(url, MODEL_ZIP, reporthook=show_progress)
        print("\n✅ 下载完成")
        return True
    except Exception as e:
        print(f"\n❌ 失败: {e}")
        if os.path.exists(MODEL_ZIP):
            os.remove(MODEL_ZIP)
        return False

# 若已解压好，直接结束
if os.path.exists(MODEL_FOLDER):
    print("✅ 模型已存在，无需重复下载。")
    sys.exit(0)

os.makedirs(MODEL_DIR, exist_ok=True)

# 依次尝试每个源
ok = False
for url in URLS:
    if try_download(url):
        ok = True
        break
    time.sleep(1)

if not ok:
    print("\n❌ 自动下载失败。请手动下载并解压到：")
    print("   下载链接（任选一个）：")
    for u in URLS:
        print("   " + u)
    sys.exit(1)

# 解压
print("📦 正在解压...")
try:
    with zipfile.ZipFile(MODEL_ZIP, 'r') as zf:
        zf.extractall(MODEL_DIR)
    os.remove(MODEL_ZIP)
    print("✅ 模型安装完成！")
except Exception as e:
    print(f"❌ 解压失败: {e}")
    sys.exit(1)
