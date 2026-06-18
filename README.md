# LightAgent — Your Local AI Computer Butler

**⚠️ Project Status: Incomplete, not fully functional, intended for academic discussion and code reference only.**  
**🔴 Important Notice: I downloaded the code from my own GitHub repository and found that many files are missing compared to my local original project. I have no idea why — possibly an upload mistake or accidental omission. Therefore, anyone building upon this repository should expect to re‑implement a significant portion of the functionality from scratch. Please be aware.**

---

## 💻 Development Environment & Hardware

- OS: Windows 10  
- CPU: Intel i5-4210H (2 cores, 4 threads)  
- GPU: NVIDIA GeForce GTX 960M (2 GB VRAM)  
- RAM: 12 GB DDR3  
- Storage: 128 GB HDD  
- Python Version: 3.11  

This project was designed, developed, debugged, and run entirely from scratch on the above old laptop. **No cloud GPU instances were used** – all inference is performed locally.

---

## 🎯 Project Background

I am a middle school student in China who just finished the high school entrance exam. **I have zero programming background.** This is my **first Python project**, completed with AI assistance, and it took me about four or five days in total.  
I did not use any dedicated AI‑programmer software (like OpenClaw – I couldn't afford it and didn't know how to use it anyway). Instead, I relied solely on ordinary DeepSeek conversations to generate code. My role was to define requirements, design the architecture, test functionalities, troubleshoot errors, and guide the iterative direction.  
To be honest, some parts are dynamically coded while others are heavily hard‑coded. The overall structure is quite messy – it’s a typical **“spaghetti code”** pile. I’ve tried my best to make it run, but the current version may not work directly in every environment. Moreover, **the code in this repository is far less complete than what I have locally** – I don't know why, so if you download it, you will likely need to rebuild many parts yourself.  
Nevertheless, I believe it can serve as a rough **architecture reference** or a starting point for **technical discussions** – it is by no means a production‑ready tool.

---

## 🎯 Project Overview

LightAgent is a **fully offline** AI desktop application that integrates a local large language model, a secure sandbox, a knowledge base, a memory system, an evolution framework, tool calling, and a training center. It understands natural language instructions and can directly control your computer (open apps, manage files, browse the web, etc.) while executing code under strict permission controls.

The original inspiration for this project came from — **being bored with nothing else to do**. With AI assistance, I completed everything from system architecture design to the development and integration of all modules on my own.

---

## ✨ Current Features

*(The following are design goals; actual operation may be impaired due to missing code.)*

- **Local Brain:** Runs entirely offline, no cloud API dependencies. Based on the Qwen2.5-1.5B GGUF model, with smooth response times.  
- **Multi‑tab GUI:** A white‑theme PyQt5 interface containing more than a dozen functional pages, including AI Console, Local Browser, Workflow Editor, Evolution Dashboard, Learning Center, Real‑time Monitor, Memory Bank, Chat Room, Local Brain Monitor, etc.  
- **Secure Sandbox:** Uses subprocess isolation to execute AI‑generated code, restricts allowed built‑in functions with a whitelist, forcibly terminates on timeout, and performs a secondary audit through a security auditor.  
- **Dynamic Enhancement Framework:** Plug‑able enhancers (Chain‑of‑Thought, Reflection, Experience Learning, RAG, etc.) significantly boost the practical capabilities of the small model.  
- **Intelligent Training Center:** Can call the DeepSeek API to automatically generate operation samples, incrementally improving the local model's task success rate. Supports manual addition and real‑time training monitoring.  
- **Evolution System:** A talent‑tree style evolution dashboard that allows users to upgrade the model's abilities (Intelligence, Speed, Safety, Creativity) with one click, and also lets advanced users write custom evolution rules.  
- **Knowledge Base & Memory:** Vector retrieval (ChromaDB) and long‑term memory management. Supports `/index` for manual indexing of local files, enabling document‑based Q&A.  
- **Tool Calling:** The model can dynamically generate tool calls in JSON format to execute sandboxed code, system commands, file operations, and web browsing.

---

## 🛠️ Development Journey

This project was built from scratch by me, with AI assistance step by step.  
The entire process was full of challenges: hundreds of syntax errors, hard‑coded paths, threading crashes, missing DLLs, memory overflows… Whenever I encountered an issue, I fed the error messages to AI, got correction suggestions, then copied, tested, and iterated repeatedly.  
The project is still evolving – the latest **MindForge** upgrade plan (heterogeneous computing, hierarchical memory, federated learning, etc.) is being gradually implemented.  
I also plan to upload a demo version later (if I can sort out the complete code), so that everyone can experience the core features more easily.

---

## 📌 Notes & Disclaimer

- The current codebase is not perfect – it contains many experimental scripts and temporary files like `fix_*.py`, and the structure is a bit messy – *laziness*, but also limited ability.  
- Some advanced modules (e.g., multimodal, federated learning) are only framework placeholders and have not yet been fully implemented.  
- **Repository code is severely incomplete** – I only realised this after downloading it myself; it seems I may have missed some files during upload. Please do not rely on this repository as a complete project.  
- The project runs completely locally, requires no network access, and ensures data privacy and security.  
- This project is more suitable as a **learning reference** or a starting point for **technical discussions** – it is not recommended for direct use in production.  
- Any suggestions, optimizations, or bug reports are highly welcome.  
- **Contact**: 158786846@qq.com
