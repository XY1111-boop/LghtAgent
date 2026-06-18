# LightAgent — Your Local AI Computer Butler

---

## ⚠️ Unified Notice (Please Read Carefully)

- **Project Status**: Incomplete, not fully functional, intended for academic discussion and code reference only.
- **Severely Missing Code**: I downloaded the code from my own GitHub repository and found that many files are missing compared to my local original project. I have no idea why (possibly an upload mistake). Therefore, anyone building upon this repository should expect to re‑implement a significant portion of the functionality from scratch. Do not rely on this repository as a complete project.
- **Not for Production**: This is a personal learning experiment with many unfixed bugs and potential security issues. **Do not use it in production or on critical systems.** The developer is not responsible for any data loss or system damage.
- **Runtime Environment**: Fully offline, all inference runs locally on an old laptop (GTX960M 2GB). No network required, privacy preserved.
- **Development Background**: The author is a middle school student with zero coding experience, assisted by AI conversations. Code quality is rough ("spaghetti code") – please be kind.
- **Recommended Use**: Better suited as an **architecture reference**, **technical discussion** material, or **teaching resource**. Direct running or deployment is not advised.

If you still wish to try, you do so at your own risk and should be prepared to re‑develop many parts.

---

## 💻 Development Environment & Hardware

- OS: Windows 10  
- CPU: Intel i5-4210H (2 cores, 4 threads)  
- GPU: NVIDIA GeForce GTX 960M (2 GB VRAM)  
- RAM: 12 GB DDR3  
- Storage: 128 GB HDD  
- Python Version: 3.11  

This project was designed, developed, debugged, and run entirely from scratch on the above old laptop. **No cloud GPU instances were used.**

---

## 🎯 Project Background

I am a middle school student in China who just finished the high school entrance exam. **I have zero programming background.** This is my **first Python project**, completed with AI assistance, and it took about four or five days.  
I did not use any dedicated AI‑programmer software (like OpenClaw); I relied solely on ordinary DeepSeek conversations to generate code. My role was to define requirements, design architecture, test, debug, and guide iterations.  
Some parts are dynamic, others are hard‑coded – the overall structure is messy, a typical "spaghetti code" pile. I tried my best, but due to missing code in the repository, it likely won't run directly after download.

---

## 🎯 Project Overview

LightAgent is a **fully offline** AI desktop application that integrates a local LLM, secure sandbox, knowledge base, memory system, evolution framework, tool calling, and training center. It understands natural language and can directly control your computer (open apps, manage files, browse the web, etc.) under strict permission controls.

The inspiration came from — **being bored**. With AI assistance, I completed everything from architecture design to module integration on my own.

---

## ✨ Current Features (Design Goals – may not all work due to missing code)

- **Local Brain**: Offline, based on Qwen2.5-1.5B GGUF.  
- **Multi‑tab GUI**: PyQt5 white theme with AI Console, Local Browser, Workflow Editor, Evolution Dashboard, Learning Center, Monitor, Memory Bank, Chat Room, Brain Monitor, etc.  
- **Secure Sandbox**: Subprocess isolation, whitelist, timeout, security auditor.  
- **Dynamic Enhancement**: Pluggable enhancers (CoT, Reflection, RAG, etc.).  
- **Training Center**: Uses DeepSeek API to generate samples, incremental learning.  
- **Evolution System**: Talent‑tree upgrades (Intelligence, Speed, Safety, Creativity).  
- **Knowledge Base & Memory**: ChromaDB vector retrieval, long‑term memory, `/index` for local files.  
- **Tool Calling**: Dynamic JSON tool calls for sandboxed code, system commands, file ops, web browsing.

---

## 🛠️ Technology Stack

- Python 3.11, PyQt5, llama‑cpp‑python, ChromaDB/FAISS, SQLite, TF‑IDF  
- Vosk (offline speech), pyttsx3 (TTS), PIL, OpenCV, pytesseract (OCR)  
- ReAct Agent, MCP protocol, L1/L2/L3 self‑evolution, federated learning (experimental)  
- Optional: DeepSeek API, Streamlit WebUI

---

## 📁 Project Structure
LightAgent/
├── main.py
├── config.yaml
├── core/ # Sandbox, executor, auditor
├── intelligence/ # LLM, memory, evolution, tools, Agent, MCP
├── knowledge/ # Vector KB, learning center
├── ui/ # All GUI tabs
├── utils/ # Config, logging, cache
├── plugins/ # Plugin system
├── skills/ # Skill YAML definitions
├── web/ # Analysis report web pages
├── models/ # Local model files (download separately)
└── tests/ # Unit tests

text

---

## 🚀 Quick Start (for Developers)

### Requirements
- Windows 10/11, Python 3.11+, GTX960M 2GB or better (CPU only works but slower), at least 12GB RAM.

### Install Dependencies
```bash
pip install -r requirements.txt
Configure API Key (Optional)
Fill in DeepSeek API Key in config.yaml or via settings UI after launch. Local models run without an API key.

Download Model
Download qwen2.5-1.5b-instruct-q4_k_m.gguf (~2.3GB) from Hugging Face mirror:
https://hf-mirror.com/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf

Place the .gguf file into the models/ directory.

Launch
bash
python main.py
Optional WebUI (Streamlit):
📚 User Manual (Common Commands)
Command	Description
你好 (Hello)	General chat
/run 打开计算器	Execute a system operation (audited and sandboxed)
/index	Manually index the knowledge base
/auto 整理桌面	Submit an autonomous task; Agent plans and executes
The Training Center can auto‑generate samples; successful /run commands are recorded as experiences to improve future success rates.
🙏 Acknowledgements
Thanks to llama‑cpp‑python, Qwen2.5, DeepSeek, ChromaDB, and all open‑source communities and AI models.

🌟 Contributing
Issues and PRs are welcome! The project is early stage – any improvements (code, docs, design) are appreciated.

💬 Contact
Email: 158786846@qq.com
bash
streamlit run webui.py
