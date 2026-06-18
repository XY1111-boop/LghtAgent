# download_vosk_model.py —— 自动下载并解压 Vosk 中文语音模型
import os, sys, zipfile, urllib.request, shutil, time

# 模型保存路径
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")

# 国内镜像源列表（自动依次尝试）
MIRRORS = [
]

def download_with_progress(url, dest):
    """带进度条的下载，支持断点续传"""
    print(f"⬇️ 尝试从 {url} 下载...")
    headers = {"User-Agent": "Mozilla/5.0"}
    resume_pos = os.path.getsize(dest) if os.path.exists(dest) else 0
    if resume_pos:
        headers["Range"] = f"bytes={resume_pos}-"
        print(f"📌 检测到部分下载，从 {resume_pos} 字节续传")

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as response, open(dest, "ab") as f:
            total_size = int(response.headers.get("content-length", 0)) + resume_pos
            block_size = 1024 * 1024  # 1MB
            downloaded = resume_pos
            while True:
                chunk = response.read(block_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                percent = int(downloaded * 100 / total_size) if total_size > 0 else 0
                sys.stdout.write(f"\r进度: {percent}% ({downloaded}/{total_size})   ")
                sys.stdout.flush()
            print()
        return True
    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        return False

# 检查模型是否已存在
if os.path.exists(MODEL_FOLDER):
    print(f"✅ 模型已存在: {MODEL_FOLDER}")
    sys.exit(0)

os.makedirs(MODEL_DIR, exist_ok=True)

# 尝试下载
success = False
for url in MIRRORS:
    if download_with_progress(url, MODEL_ZIP):
        success = True
        break
    else:
        # 删除可能的不完整文件
        if os.path.exists(MODEL_ZIP):
            os.remove(MODEL_ZIP)

if not success:
    print("\n❌ 所有镜像下载失败，请检查网络或稍后重试。")
    sys.exit(1)

# 解压
print("📦 正在解压模型...")
try:
    with zipfile.ZipFile(MODEL_ZIP, 'r') as zip_ref:
        zip_ref.extractall(MODEL_DIR)
    print("✅ 解压完成")
    # 删除压缩包
    os.remove(MODEL_ZIP)
    print("🗑️ 已删除压缩包")
except Exception as e:
    print(f"❌ 解压失败: {e}")
    sys.exit(1)

print("\n🎉 Vosk 中文语音模型已就绪！")
print("现在可以重启 LightAgent，虚拟主播将拥有完全离线的语音识别能力。")
