# webui.py —— Streamlit 多面板界面
import streamlit as st
from intelligence.inference_engine import InferenceEngine
from intelligence.agent_loop import AgentLoop
from ui.workspace_agent import WorkspaceAgent

def main():
    st.set_page_config(page_title="Y50p‑MindForge", layout="wide")
    st.title("🧠 Y50p‑MindForge")

    tab1, tab2, tab3, tab4 = st.tabs(["对话", "工作区", "Agent", "系统"])

    with tab1:
        st.header("聊天")
        user_input = st.text_input("你:")
        if user_input:
            engine = InferenceEngine("models")
            response = engine.chat([{"role": "user", "content": user_input}])
            st.write(f"张瑶瑶: {response}")

    with tab2:
        st.header("AI 编程工作区")
        workspace = WorkspaceAgent("E:/LightAgent/workspace")
        if st.button("扫描项目"):
            files = workspace.scan_project()
            st.json(files)

    with tab3:
        st.header("Agent 控制台")
        goal = st.text_input("目标:")
        if goal:
            engine = InferenceEngine("models")
            tools = ToolRegistry()
            memory = HierarchicalMemory()
            agent = AgentLoop(engine, tools, memory)
            result = agent.run(goal)
            st.write(result)

    with tab4:
        st.header("系统健康")
        st.write("GPU 显存使用: ...")
        st.write("内存使用: ...")

if __name__ == "__main__":
    main()
