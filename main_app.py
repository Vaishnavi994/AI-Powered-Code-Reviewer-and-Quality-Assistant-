import streamlit as st
import multiprocessing
import tkinter as tk
from tkinter import filedialog
import os

def _picker_process(queue):
    """This function runs in a completely separate OS process."""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
    root.destroy()
    queue.put(path)

def get_file_path_safely():
    """Starts a process to pick a file and waits for the result."""
    queue = multiprocessing.Queue()
    p = multiprocessing.Process(target=_picker_process, args=(queue,))
    p.start()
    path = queue.get() # Wait for the user to pick
    p.join()
    return path

# --- Inside your Streamlit UI ---
if st.button("📂 Browse Local File"):
    path = get_file_path_safely()
    if path:
        st.session_state.file_path = path
        with open(path, "r", encoding="utf-8") as f:
            st.session_state.uploaded_code = f.read()
        st.rerun()

if st.session_state.get("file_path"):
    st.info(f"Targeting: {st.session_state.file_path}")
    
    if st.button("💾 Overwrite Original File"):
        with open(st.session_state.file_path, "w", encoding="utf-8") as f:
            f.write(st.session_state.uploaded_code)
        st.success("File updated on disk!")