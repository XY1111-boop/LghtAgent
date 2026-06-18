# webui.py —— Streamlit 多面板界面（根目录运行）
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

def main():
    st.set_page_config(page_title="Y50p‑MindForge", layout="wide")
    st.title("🧠 Y50p‑MindForge 控制台")

    tab1, tab2, tab3, tab4 = st.tabs(["对话", "工作区", "Agent", "系统"])

    with tab1:
        st.header("聊天")
        user_input = st.text_input("你:")
        if user_input:
            # 动态导入引擎
            from intelligence.inference_engine import InferenceEngine
            engine = InferenceEngine("models")
            response = engine.chat([{"role": "user", "content": user_input}])
            st.write(f"张瑶瑶: {response}")

    with tab2:
        st.header("AI 编程工作区")
        from intelligence.workspace_agent import WorkspaceAgent
        workspace = WorkspaceAgent("E:/LightAgent/workspace")
        if st.button("扫描项目"):
            files = workspace.scan_project()
            st.json(files)

    with tab3:
        st.header("Agent 控制台")
        goal = st.text_input("目标:")
        if goal:
            from intelligence.inference_engine import InferenceEngine
            from intelligence.tool_registry import ToolRegistry
            from intelligence.memory_store import HierarchicalMemory
            from intelligence.agent_loop import AgentLoop
            engine = InferenceEngine("models")
            tools = ToolRegistry()
            memory = HierarchicalMemory()
            agent = AgentLoop(engine, tools, memory)
            result = agent.run(goal)
            st.write(result)

    with tab4:
        st.header("系统健康")
        import psutil, GPUtil
        mem = psutil.virtual_memory().percent
        cpu = psutil.cpu_percent()
        st.metric("CPU", f"{cpu}%")
        st.metric("内存", f"{mem}%")
        try:
            gpu = GPUtil.getGPUs()[0]
            st.metric("GPU", f"{gpu.memoryUtil*100:.0f}%")
        except:
            st.write("无 GPU 数据")

if __name__ == "__main__":
    main()
