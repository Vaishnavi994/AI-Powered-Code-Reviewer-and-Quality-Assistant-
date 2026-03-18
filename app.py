import streamlit as st
import pandas as pd
import os
import multiprocessing
import tkinter as tk
from tkinter import filedialog
import plotly.express as px
import ast
import astor
import textwrap
import subprocess
import json

from parser.findfunctions import extract_functions
from validation.code_analyzer import fix_source_code
from parser.file_parser import get_function_node
from docstring_engine.docstring_generator import (
    remove_existing_docstring,
    generate_docstring,
    insert_docstring,
    update_function_in_file
)
from docstring_engine.docstring_inserter import insert_or_update_docstring

# ----------------------------
# Native File/Folder Picker
# ----------------------------
def _picker_process(queue, mode="file"):
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    if mode == "folder":
        path = filedialog.askdirectory()
    else:
        path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])

    root.destroy()
    queue.put(path)


def get_path_safely(mode="file"):
    queue = multiprocessing.Queue()
    p = multiprocessing.Process(target=_picker_process, args=(queue, mode))
    p.start()
    path = queue.get()
    p.join()
    return path


# ----------------------------
# Streamlit Config
# ----------------------------
st.set_page_config(page_title="AI Python Studio", page_icon="💎", layout="wide")


# ----------------------------
# Ultra Modern Dashboard Styling
# ----------------------------
# st.markdown("""
# <style>

# /* App Background */
# .stApp{
# background:linear-gradient(135deg,#f8fafc,#eef2ff,#f0f9ff);
# font-family: 'Inter', sans-serif;
# }

# /* Title */
# h1{
# font-weight:800;
# letter-spacing:-0.5px;
# color:#1e293b;
# }

# /* Section titles */
# h2,h3{
# color:#1e3a8a;
# font-weight:700;
# }

# /* Metric cards */
# div[data-testid="metric-container"]{
# background:linear-gradient(145deg,#ffffff,#f8fafc);
# border:1px solid #e5e7eb;
# padding:22px;
# border-radius:18px;
# box-shadow:0 10px 25px rgba(0,0,0,0.05);
# transition:all .25s ease;
# }

# div[data-testid="metric-container"]:hover{
# transform:translateY(-6px);
# box-shadow:0 14px 35px rgba(0,0,0,0.08);
# }

# [data-testid="stMetricValue"]{
# color:#2563eb;
# font-weight:800;
# }

# /* Buttons */
# div.stButton > button{
# background:linear-gradient(135deg,#3b82f6,#6366f1);
# color:white;
# border-radius:14px;
# border:none;
# height:3.3em;
# font-weight:600;
# font-size:15px;
# transition:all .25s ease;
# box-shadow:0 6px 18px rgba(0,0,0,0.1);
# }

# div.stButton > button:hover{
# transform:translateY(-3px);
# box-shadow:0 10px 25px rgba(0,0,0,0.15);
# }

# /* Dropdown */
# div[data-baseweb="select"]{
# border-radius:10px;
# }

# /* Tabs */
# button[data-baseweb="tab"]{
# font-weight:600;
# font-size:15px;
# }

# /* Docstring comparison cards */

# .doc-card{
# border-radius:14px;
# padding:18px;
# height:420px;
# overflow-y:auto;
# font-family:Courier New;
# font-size:14px;
# white-space:pre-wrap;
# box-shadow:0 6px 18px rgba(0,0,0,0.05);
# transition:all .2s ease;
# }

# .doc-card:hover{
# transform:scale(1.01);
# }

# /* BEFORE */
# .before-box{
# background:#ffffff;
# border:1px solid #e5e7eb;
# color:#1e293b;
# }

# /* AFTER */
# .after-box{
# background:#eff6ff;
# border:1px solid #93c5fd;
# color:#1d4ed8;
# }

# /* Issue cards */
# .issue-card{
# background:#fff1f2;
# border-left:5px solid #f43f5e;
# padding:15px;
# border-radius:10px;
# margin-bottom:10px;
# color:#9f1239;
# font-size:14px;
# }

# /* File panel */
# .file-panel{
# background:white;
# border-radius:12px;
# padding:12px;
# border:1px solid #e5e7eb;
# box-shadow:0 3px 12px rgba(0,0,0,0.05);
# }

# /* Smooth animation */
# @keyframes fadeIn{
# from{opacity:0;transform:translateY(10px);}
# to{opacity:1;transform:translateY(0);}
# }

# .block-container{
# animation:fadeIn .4s ease;
# }
            

# </style>
# """, unsafe_allow_html=True)
st.markdown("""
<style>

/* -------- GLOBAL APP -------- */

.stApp{
background:linear-gradient(135deg,#f1f5f9,#eef2ff,#ecfeff);
font-family:'Inter',sans-serif;
color:#1e293b;
}

/* Smooth page animation */
.block-container{
animation:fadeIn .45s ease;
}

/* -------- TITLE -------- */

h1{
font-weight:900;
letter-spacing:-1px;
font-size:40px;
background:linear-gradient(90deg,#3b82f6,#6366f1);
-webkit-background-clip:text;
-webkit-text-fill-color:transparent;
}

h2,h3{
font-weight:700;
color:#1e3a8a;
}

/* -------- METRIC CARDS -------- */

div[data-testid="metric-container"]{
background:linear-gradient(145deg,#ffffff,#f8fafc);
border:1px solid #e2e8f0;
padding:24px;
border-radius:18px;
box-shadow:0 15px 40px rgba(0,0,0,0.06);
transition:all .3s ease;
}

div[data-testid="metric-container"]:hover{
transform:translateY(-8px) scale(1.02);
box-shadow:0 25px 50px rgba(0,0,0,0.12);
}

[data-testid="stMetricValue"]{
font-size:32px;
font-weight:800;
color:#2563eb;
}

/* -------- BUTTONS -------- */

div.stButton > button{
background:linear-gradient(135deg,#6366f1,#3b82f6);
color:white;
border:none;
border-radius:14px;
height:3.3em;
font-weight:600;
font-size:15px;
transition:all .25s ease;
box-shadow:0 8px 20px rgba(0,0,0,0.12);
}

div.stButton > button:hover{
transform:translateY(-4px) scale(1.02);
box-shadow:0 14px 30px rgba(0,0,0,0.18);
}

/* -------- SIDEBAR PANELS -------- */

.file-panel{
background:white;
border-radius:14px;
padding:14px;
border:1px solid #e2e8f0;
box-shadow:0 6px 18px rgba(0,0,0,0.06);
}

/* -------- DOCSTRING CARDS -------- */

.doc-card{
border-radius:16px;
padding:18px;
height:420px;
overflow-y:auto;
font-family:Courier New;
font-size:14px;
white-space:pre-wrap;
box-shadow:0 10px 28px rgba(0,0,0,0.08);
transition:all .2s ease;
}

.doc-card:hover{
transform:scale(1.01);
}

/* BEFORE BOX */

.before-box{
background:linear-gradient(180deg,#ffffff,#f8fafc);
border:1px solid #e2e8f0;
color:#1e293b;
}

/* AFTER BOX */

.after-box{
background:linear-gradient(180deg,#eff6ff,#dbeafe);
border:1px solid #60a5fa;
color:#1e40af;
}

/* -------- ISSUE CARDS -------- */

.issue-card{
background:#fff1f2;
border-left:5px solid #f43f5e;
padding:15px;
border-radius:12px;
margin-bottom:10px;
color:#9f1239;
font-size:14px;
box-shadow:0 4px 12px rgba(0,0,0,0.05);
}

/* -------- DASHBOARD HERO -------- */

.hero-card{
padding:30px;
border-radius:20px;
background:linear-gradient(135deg,#6366f1,#8b5cf6);
color:white;
font-size:32px;
font-weight:800;
box-shadow:0 18px 50px rgba(0,0,0,0.2);
}

/* -------- TABS -------- */

button[data-baseweb="tab"]{
font-weight:600;
font-size:15px;
}

/* -------- SCROLLBAR -------- */

::-webkit-scrollbar{
width:6px;
}

::-webkit-scrollbar-thumb{
background:#94a3b8;
border-radius:10px;
}

/* -------- ANIMATION -------- */

@keyframes fadeIn{
from{
opacity:0;
transform:translateY(10px);
}
to{
opacity:1;
transform:translateY(0);
}
}

</style>
""", unsafe_allow_html=True)

# ----------------------------
# Helper Styling
# ----------------------------
def color_docstring(val):
    color = '#dcfce7' if val == "✅ Present" else '#fee2e2'
    text_color = '#166534' if val == "✅ Present" else '#991b1b'
    return f'background-color: {color}; color: {text_color}; font-weight: bold;'


def get_project_status(df):
    if df.empty:
        return "No Data", "#9ca3af"

    doc_percent = (len(df[df["Docstring"] == "✅ Present"]) / len(df)) * 100
    avg_complexity = df["Complexity"].mean()
    total_violations = df["Violations"].sum()

    score = doc_percent - (avg_complexity * 2) - (total_violations * 3)

    if score >= 60:
        return "🟢 Good", "#16a34a"
    elif score >= 30:
        return "🟡 Average", "#ca8a04"
    else:
        return "🔴 Poor", "#dc2626"


# ----------------------------
# Session State
# ----------------------------
for key in ["file_path", "analysis_done", "master_data", "project_errors", "file_contents"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key in ["master_data", "project_errors"] else False if key=="analysis_done" else {}


# ----------------------------
# FULL ANALYSIS FUNCTION
# ----------------------------
def run_full_analysis():

    files = []
    if os.path.isdir(st.session_state.file_path):
        for root_dir, _, fnames in os.walk(st.session_state.file_path):
            for f in fnames:
                if f.endswith(".py"):
                    files.append(os.path.join(root_dir, f))
    else:
        files.append(st.session_state.file_path)

    master_data = []
    project_errors = []
    file_contents = {}

    for f in files:
        with open(f, "r", encoding="utf-8") as file:
            content = file.read()
            file_contents[f] = content

        errs, _ = fix_source_code(content, os.path.basename(f))
        raw_functions = extract_functions(f, original_name=os.path.basename(f))

        for r in raw_functions:
            master_data.append({
                "File": r["file_name"],
                "Function": r["function_name"],
                "Start Line": r.get("start_line"),
                "End Line": r.get("end_line"),
                "Complexity": r["cyclomatic_complexity"],
                "Violations": len(r["errors"]),
                "Docstring": "✅ Present" if r["has_docstring"] else "❌ Missing"
            })

        if errs:
            project_errors.extend([(os.path.basename(f), e) for e in errs])
       

    st.session_state.master_data = master_data
    
    st.session_state.project_errors = project_errors
    st.session_state.file_contents = file_contents
    st.session_state.analysis_done = True


# ----------------------------
# UI
# ----------------------------
# st.title("💎 AI Python Code Studio")
# st.markdown("---")
st.markdown("""
<div class="hero-card">
💎 AI Python Code Studio
<div style="font-size:16px;font-weight:400;margin-top:10px;">
AI-powered code analysis • Documentation • Testing • Quality Insights
</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

left, right = st.columns([1, 2.8])

with left:

    st.subheader("📁 1. Select Source")

    c1, c2 = st.columns(2)

    with c1:
        if st.button("📄 File", use_container_width=True):
            st.session_state.file_path = get_path_safely("file")
            st.session_state.analysis_done = False

    with c2:
        if st.button("📁 Folder", use_container_width=True):
            st.session_state.file_path = get_path_safely("folder")
            st.session_state.analysis_done = False

    if st.session_state.file_path:
        st.success(f"📍 Target: {os.path.basename(st.session_state.file_path)}")

    action = st.selectbox(
    "Choose Action",
    [
        "-- Select --",
        "📊 Dashboard",
        "🏠 Home Overview",
        "📊 Function Analysis",
        "🔥 Code Quality Dashboard",
        "📘 Docstring Review"
    ]
    )

    if st.button("🚀 Analyze Code", use_container_width=True):
        if st.session_state.file_path:
            with st.spinner("🔍 Analyzing Project..."):
                run_full_analysis()
            st.success("✅ Analysis Complete!")


# ----------------------------
# RIGHT PANEL
# ----------------------------
with right:

    if st.session_state.analysis_done:

        df = pd.DataFrame(st.session_state.master_data)
        # ---------------- DASHBOARD ----------------
        # ---------------- DASHBOARD ----------------
        if action == "📊 Dashboard":

            st.markdown("""
            <div style="
            padding:35px;
            border-radius:18px;
            background:linear-gradient(135deg,#6366f1,#8b5cf6);
            color:white;
            font-size:32px;
            font-weight:bold;
            ">
            📊 Dashboard
            <div style="font-size:16px;font-weight:400;margin-top:10px;">
            Advanced tools for code analysis and management
            </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("### 🧭 Dashboard Navigation")

            nav1, nav2, nav3, nav4, nav5 = st.columns(5)

            with nav1:
                if st.button("🔎 Filters", use_container_width=True):
                    st.session_state.dashboard_view = "filters"

            with nav2:
                if st.button("🔍 Search", use_container_width=True):
                    st.session_state.dashboard_view = "search"

            with nav3:
                if st.button("🧪 Tests", use_container_width=True):
                    st.session_state.dashboard_view = "tests"

            with nav4:
                if st.button("📦 Export", use_container_width=True):
                    st.session_state.dashboard_view = "export"

            with nav5:
                if st.button("ℹ️ Help", use_container_width=True):
                    st.session_state.dashboard_view = "help"

            st.markdown("---")

            df = pd.DataFrame(st.session_state.master_data)

            view = st.session_state.get("dashboard_view", None)

            # ---------------- FILTERS ----------------
            if view == "filters":

                st.subheader("🔎 Function Filters")

                if df.empty:
                    st.warning("Run analysis first.")
                else:

                    col1, col2 = st.columns(2)

                    with col1:
                        max_complexity = st.slider(
                            "Maximum Complexity",
                            0,
                            int(df["Complexity"].max()),
                            int(df["Complexity"].max())
                        )

                    with col2:
                        doc_filter = st.selectbox(
                            "Docstring Status",
                            ["All", "Present", "Missing"]
                        )

                    filtered_df = df.copy()

                    filtered_df = filtered_df[
                        filtered_df["Complexity"] <= max_complexity
                    ]

                    if doc_filter == "Present":
                        filtered_df = filtered_df[
                            filtered_df["Docstring"] == "✅ Present"
                        ]

                    elif doc_filter == "Missing":
                        filtered_df = filtered_df[
                            filtered_df["Docstring"] == "❌ Missing"
                        ]

                    st.dataframe(filtered_df, use_container_width=True)

            # ---------------- SEARCH ----------------
            elif view == "search":

                st.subheader("🔍 Function Search")

                if df.empty:
                    st.warning("Run analysis first.")
                else:

                    query = st.text_input("Search Function Name")

                    if query:

                        results = df[
                            df["Function"].str.contains(query, case=False)
                        ]

                        st.write("Results Found:", len(results))

                        st.dataframe(results, use_container_width=True)
            # ---------------- EXPORT ----------------
            elif view == "export":

                st.subheader("📦 Export Analysis")

                if df.empty:
                    st.warning("Run analysis first.")
                else:

                    # File paths
                    STORAGE_FOLDER = "storage"
                    csv_path = os.path.join(STORAGE_FOLDER, "analysis_report.csv")
                    json_path = os.path.join(STORAGE_FOLDER, "analysis_report.json")

                    # Generate data
                    csv_data = df.to_csv(index=False)
                    json_data = df.to_json(orient="records", indent=2)

                    # Save automatically to storage folder
                    with open(csv_path, "w", encoding="utf-8") as f:
                        f.write(csv_data)

                    with open(json_path, "w", encoding="utf-8") as f:
                        f.write(json_data)

                    st.success(f"Files saved to storage folder: `{STORAGE_FOLDER}`")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.download_button(
                            "⬇ Download CSV",
                            data=csv_data,
                            file_name="analysis_report.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

                    with col2:
                        st.download_button(
                            "⬇ Download JSON",
                            data=json_data,
                            file_name="analysis_report.json",
                            mime="application/json",
                            use_container_width=True
                        )
             
            elif view == "tests":

                st.subheader("🧪 Code Test Dashboard")

                run_tests = st.button("🚀 Run Tests")

                if run_tests:

                    with st.spinner("Running tests..."):

                        subprocess.run(
                            ["pytest", "--json-report", "--json-report-file=storage/test_report.json"],
                            capture_output=True,
                            text=True
                        )

                    st.success("Tests completed")

                    report_path = "storage/test_report.json"

                    if os.path.exists(report_path):

                        with open(report_path) as f:
                            report = json.load(f)

                        # tests = report["summary"]["total"]
                        # passed = report["summary"]["passed"]
                        # failed = report["summary"]["failed"]
                        summary = report.get("summary", {})

                        tests = summary.get("total", 0)
                        passed = summary.get("passed", 0)
                        failed = summary.get("failed", 0)

                        col1, col2, col3 = st.columns(3)

                        col1.metric("Total Tests", tests)
                        col2.metric("Passed", passed)
                        col3.metric("Failed", failed)

                        st.markdown("---")

                        # -------- Test Results by File --------

                        file_results = {}

                        for test in report["tests"]:
                            file = test["nodeid"].split("::")[0]

                            if file not in file_results:
                                file_results[file] = {"passed":0,"failed":0}

                            if test["outcome"] == "passed":
                                file_results[file]["passed"] += 1
                            else:
                                file_results[file]["failed"] += 1

                        files = list(file_results.keys())
                        passed_counts = [file_results[f]["passed"] for f in files]
                        failed_counts = [file_results[f]["failed"] for f in files]

                        import plotly.graph_objects as go

                        fig = go.Figure()

                        fig.add_trace(go.Bar(
                            x=files,
                            y=passed_counts,
                            name="Passed"
                        ))

                        fig.add_trace(go.Bar(
                            x=files,
                            y=failed_counts,
                            name="Failed"
                        ))

                        fig.update_layout(
                            barmode="group",
                            template="plotly_dark",
                            xaxis_title="Test File",
                            yaxis_title="Tests"
                        )

                        st.plotly_chart(fig, use_container_width=True)

                        # -------- Test Suite Panel --------

                        st.markdown("### 📋 Test Suites")

                        for f in files:

                            p = file_results[f]["passed"]
                            fl = file_results[f]["failed"]
                            total = p + fl

                            color = "#065f46" if fl == 0 else "#7f1d1d"

                            st.markdown(
                                f"""
                                <div style="
                                background:{color};
                                padding:14px;
                                border-radius:10px;
                                margin-bottom:10px;
                                color:white;
                                display:flex;
                                justify-content:space-between;
                                ">
                                <span>{f}</span>
                                <span>{p}/{total} passed</span>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
            # # ---------------- TESTS ----------------
            # elif view == "tests":

            #     st.subheader("🧪 Code Testing")

            #     if df.empty:
            #         st.warning("Run analysis first.")
            #     else:

            #         if st.button("Run Quick Test", use_container_width=True):

            #             total_functions = len(df)
            #             avg_complexity = df["Complexity"].mean()
            #             violations = df["Violations"].sum()

            #             st.success("Tests Completed Successfully")

            #             col1, col2, col3 = st.columns(3)

            #             col1.metric("Functions", total_functions)
            #             col2.metric("Avg Complexity", round(avg_complexity, 2))
            #             col3.metric("Violations", violations)

            # # ---------------- EXPORT ----------------
            # elif view == "export":

            #     st.subheader("📦 Export Analysis")

            #     if df.empty:
            #         st.warning("Run analysis first.")
            #     else:

            #         csv = df.to_csv(index=False)

            #         st.download_button(
            #             "Download CSV",
            #             data=csv,
            #             file_name="analysis_report.csv",
            #             mime="text/csv",
            #             use_container_width=True
            #         )

            #         json_data = df.to_json(orient="records", indent=2)

            #         st.download_button(
            #             "Download JSON",
            #             data=json_data,
            #             file_name="analysis_report.json",
            #             mime="application/json",
            #             use_container_width=True
            #         )

            # ---------------- HELP ----------------
            elif view == "help":

                st.subheader("ℹ️ Help")

                st.markdown("""
                ### 📊 Dashboard Guide

                **🔎 Filters**
                - Filter functions by complexity
                - Filter by docstring availability

                **🔍 Search**
                - Quickly locate functions by name

                **🧪 Tests**
                - Run quick code quality checks

                **📦 Export**
                - Download results as CSV or JSON

                **📘 Docstring Review**
                - Automatically generate documentation
                """)
                    
                
        # ---------------- HOME ----------------
        elif action == "🏠 Home Overview":

            st.subheader("🏠 Project Overview")

            status, color = get_project_status(df)

            st.markdown(
                f"""
                <div style="padding:20px;border-radius:12px;
                background-color:{color}20;
                border:2px solid {color};
                font-size:20px;font-weight:bold;color:{color}">
                Project Status: {status}
                </div>
                """,
                unsafe_allow_html=True
            )

            m1, m2, m3 = st.columns(3)

            m1.metric("📦 Functions", len(df))
            m2.metric("🔥 Violations", int(df["Violations"].sum()))
            m3.metric(
                "📝 Docstrings %",
                f"{(len(df[df['Docstring']=='✅ Present'])/len(df)*100):.0f}%"
            )

        # ---------------- FUNCTION ANALYSIS ----------------
        elif action == "📊 Function Analysis":

            tab1, tab2 = st.tabs(["📋 Table View", "🧾 JSON View"])

            with tab1:
                st.dataframe(
                    df.style.applymap(color_docstring, subset=['Docstring']),
                    use_container_width=True
                )

            with tab2:
                st.json(df.to_dict(orient="records"))
                st.download_button(
                    "⬇ Download JSON",
                    data=df.to_json(orient="records", indent=2),
                    file_name="function_analysis.json",
                    mime="application/json",
                    use_container_width=True
                )



        elif action == "📘 Docstring Review":   
            st.subheader("📘 AI Docstring Assistant")

            st.markdown(
                """
                <div style="padding:15px;border-radius:10px;background:#f8fafc;
                border:1px solid #e2e8f0;margin-bottom:15px">
                Select a documentation style and review or generate docstrings for functions.
                </div>
                """,
                unsafe_allow_html=True
            )

            # -------- STYLE SELECTOR (FORCED REFRESH) --------
            # style_tabs = ["📘 Google Style", "📗 NumPy Style", "📙 reST Style"]
            
            # # Using a unique key ensures reST style triggers a rerun instantly
            # style_choice = st.radio("Select Docstring Style", style_tabs, horizontal=True, key="style_sync_key")

            # style_map = {"📘 Google Style": "Google", "📗 NumPy Style": "NumPy", "📙 reST Style": "reST"}
            # current_style = style_map[style_choice]
            st.markdown("### ✨ Choose Documentation Style")

            col1, col2, col3 = st.columns(3)

            if "doc_style" not in st.session_state:
                st.session_state.doc_style = "Google"

            # with col1:
            #     if st.button("📘 Google Style", use_container_width=True):
            #         st.session_state.doc_style = "Google"

            # with col2:
            #     if st.button("📗 NumPy Style", use_container_width=True):
            #         st.session_state.doc_style = "NumPy"

            # with col3:
            #     if st.button("📙 reST Style", use_container_width=True):
            #         st.session_state.doc_style = "reST"
            with col1:
                if st.button("📘 Google Style", use_container_width=True):
                    st.session_state.doc_style = "Google"
                    st.rerun()

            with col2:
                if st.button("📗 NumPy Style", use_container_width=True):
                    st.session_state.doc_style = "NumPy"
                    st.rerun()

            with col3:
                if st.button("📙 reST Style", use_container_width=True):
                    st.session_state.doc_style = "reST"
                    st.rerun()

            current_style = st.session_state.doc_style
            if "last_style" not in st.session_state:
                st.session_state.last_style = current_style

            if st.session_state.last_style != current_style:
                st.session_state.doc_cache = {}   # clear old cache
                st.session_state.last_style = current_style

            st.caption(f"Selected Style: **{current_style}**")
            
            # Update session state immediately
            st.session_state.doc_style = current_style

            st.caption(f"Selected Documentation Style: **{st.session_state.doc_style}**")
            st.markdown("---")

            df = pd.DataFrame(st.session_state.master_data)

            if df.empty:
                st.warning("No data available. Run analysis first.")
            else:
                left_col, right_col = st.columns([1, 2])

                with left_col:
                    st.markdown("### 📁 Project Files")
                    file_groups = df.groupby("File")
                    selected_file = st.selectbox("Select File", list(file_groups.groups.keys()))
                    file_df = file_groups.get_group(selected_file)
                    needed_count = len(file_df[file_df["Docstring"] == "❌ Missing"])

                    st.markdown(
                        f"""
                        <div style="padding:12px;border-radius:10px;background:#eef2ff;border:1px solid #c7d2fe">
                        Functions in File: <b>{len(file_df)}</b><br>
                        Missing Docstrings: <b>{needed_count}</b>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with right_col:
                    st.markdown("### ⚙️ Function Review")
                    selected_function = st.selectbox("Select Function", file_df["Function"].tolist())
                    func_row = file_df[file_df["Function"] == selected_function].iloc[0]

                    is_doc = func_row["Docstring"] == "✅ Present"
                    status_bg = "#dcfce7" if is_doc else "#fee2e2"
                    status_text = "#166534" if is_doc else "#991b1b"
                    status_label = "Documented" if is_doc else "Missing"

                    st.markdown(
                        f"""
                        <div style="padding:12px; border-radius:10px; background-color:#f1f5f9; border:1px solid #e2e8f0; 
                        display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:600; color:#1e293b;">Function: <span style="color:#2563eb;">{selected_function}</span></span>
                            <span style="background:{status_bg}; color:{status_text}; padding:2px 12px; border-radius:15px; font-size:0.85rem; font-weight:bold; border:1px solid {status_text}40;">
                                {status_label}
                            </span>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )

                st.markdown("---")
                st.markdown("### 📄 Docstring Comparison")

                file_path = next((f for f in st.session_state.file_contents if os.path.basename(f) == selected_file), None)

                if file_path:
                    with open(file_path, "r", encoding="utf-8") as file:
                        source_code = file.read()

                    tree = ast.parse(source_code)
                    node = get_function_node(tree, selected_function)
                    current_doc = ast.get_docstring(node) if node else None

                    if node and hasattr(node, "lineno"):
                        try:
                            function_code = ast.get_source_segment(source_code, node) or ""
                        except Exception: function_code = ""
                    else: function_code = ""

                   
                    # generated_doc = generate_docstring(function_code, current_style)
                    # -------- FIXED DOCSTRING GENERATION --------

                    doc_cache_key = f"{selected_file}_{selected_function}_{current_style}"

                    if "doc_cache" not in st.session_state:
                        st.session_state.doc_cache = {}

                    # Generate ONLY if not already generated for this style
                    if doc_cache_key not in st.session_state.doc_cache:
                        with st.spinner("Generating docstring..."):
                            st.session_state.doc_cache[doc_cache_key] = generate_docstring(function_code, current_style)

                    generated_doc = st.session_state.doc_cache[doc_cache_key]

                    # --- UI DISPLAY ---
                    doc_col1, doc_col2 = st.columns(2)

                    with doc_col1:
                        st.markdown("#### 📜 Current")
                        curr_val = current_doc if current_doc else "No docstring found."
                        st.markdown(
                            f"""
                            <div style="border-radius:10px; border:1px solid #e2e8f0; padding:15px; background:white; 
                            height:400px; overflow-y:auto; font-family:'Courier New', monospace; font-size:15px; font-weight:500; color:#1e293b; white-space:pre-wrap;">{curr_val}</div>
                            """, 
                            unsafe_allow_html=True
                        )
                        doc_cache_key = f"{selected_file}_{selected_function}_{current_style}"

                        if doc_cache_key not in st.session_state.doc_cache:
                            with st.spinner("Generating docstring..."):
                                st.session_state.doc_cache[doc_cache_key] = generate_docstring(function_code, current_style)

                        generated_doc = st.session_state.doc_cache[doc_cache_key]

                    with doc_col2:
                        st.markdown(f"#### ✨ AI Generated ({current_style})")
                        st.markdown(
                            f"""
                            <div style="border-radius:10px; border:1px solid #bae6fd; padding:15px; background:#f0f9ff; 
                            height:400px; overflow-y:auto; font-family:Courier New; font-size:15px; color:#0369a1; white-space:pre-wrap;">\"\"\"\n{generated_doc}\n\"\"\"</div>
                            """, 
                            unsafe_allow_html=True
                        )

                    st.markdown("<br>", unsafe_allow_html=True)

                    # ---------------- ACTION BUTTONS ----------------
                    btn1, btn2 = st.columns(2)
                    with btn1:
                        if st.button("💾 Insert / Update Docstring", use_container_width=True, type="primary"):
                            clean_code = remove_existing_docstring(function_code)
                            # final_doc = generate_docstring(clean_code, current_style)
                            doc_cache_key = f"{selected_file}_{selected_function}_{current_style}"
                            final_doc = st.session_state.doc_cache.get(doc_cache_key) or generate_docstring(clean_code, current_style)
                            new_func = insert_docstring(clean_code, final_doc)
                            update_function_in_file(file_path, selected_function, new_func)
                            run_full_analysis()
                            st.rerun()

                    # with btn2:
                    #     if st.button("🚀 Update All Functions", use_container_width=True):
                    #         # Batch logic using current_style
                    #         # df_file = df[df["File"] == selected_file]
                    #         cache_key = f"{selected_file}_{func_name}_{current_style}"
                    #         d_doc = st.session_state.doc_cache.get(cache_key) or generate_docstring(c_code, current_style)
                    #         for func_name in df_file["Function"].tolist():
                    #             with open(file_path, "r", encoding="utf-8") as f:
                    #                 src = f.read()
                    #             t = ast.parse(src)
                    #             n = get_function_node(t, func_name)
                    #             if n:
                    #                 f_code = ast.get_source_segment(src, n) or ""
                    #                 c_code = remove_existing_docstring(f_code)
                    #                 d_doc = generate_docstring(c_code, current_style)
                    #                 u_func = insert_docstring(c_code, d_doc)
                    #                 update_function_in_file(file_path, func_name, u_func)
                    #         run_full_analysis()
                    #         st.balloons()
                    #         st.rerun()
                    with btn2:
                        if st.button("🚀 Update All Functions", use_container_width=True):

                            df_file = df[df["File"] == selected_file]

                            for func_name in df_file["Function"].tolist():

                                with open(file_path, "r", encoding="utf-8") as f:
                                    src = f.read()

                                t = ast.parse(src)
                                n = get_function_node(t, func_name)

                                if n:
                                    f_code = ast.get_source_segment(src, n) or ""
                                    c_code = remove_existing_docstring(f_code)

                                    cache_key = f"{selected_file}_{func_name}_{current_style}"

                                    # ✅ Use cache properly
                                    if cache_key not in st.session_state.doc_cache:
                                        st.session_state.doc_cache[cache_key] = generate_docstring(c_code, current_style)

                                    d_doc = st.session_state.doc_cache[cache_key]

                                    u_func = insert_docstring(c_code, d_doc)
                                    update_function_in_file(file_path, func_name, u_func)

                            run_full_analysis()
                            st.balloons()
                            st.rerun()




   

        # ---------------- DASHBOARD ----------------
        elif action == "🔥 Code Quality Dashboard":

            tab1, tab2 = st.tabs(["🚨 Errors & Fix Code", "📈 Graph Insights"])

            with tab1:

                if st.session_state.project_errors:

                    grouped = {}
                    for f, e in st.session_state.project_errors:
                        grouped.setdefault(f, []).append(e)

                    for file_name, errors in grouped.items():
                        with st.expander(f"📄 {file_name} ({len(errors)} Errors)"):
                            for e in errors:
                                st.markdown(
                                    f'<div class="issue-card">❌ {e}</div>',
                                    unsafe_allow_html=True
                                )

                    if st.button("🔥 FIX ERRORS", type="primary", use_container_width=True):

                        for f_path in st.session_state.file_contents:

                            original = st.session_state.file_contents[f_path]
                            _, fixed = fix_source_code(original, os.path.basename(f_path))

                            with open(f_path, "w", encoding="utf-8") as file:
                                file.write(fixed)

                        run_full_analysis()
                        st.success("✅ Errors Fixed & Dashboard Updated!")
                        st.balloons()
                        st.rerun()
                else:
                    st.success("✨ No issues found.")

            with tab2:

                if not df.empty:

                    st.subheader("📈 Code Quality Insights")
                    st.markdown("### 📊 Bar Graph Analysis")

                    color_seq = px.colors.qualitative.Set2

                    col1, col2 = st.columns(2)

                    with col1:
                        fig_bar_complexity = px.bar(
                            df,
                            x="Function",
                            y="Complexity",
                            color="Function",
                            color_discrete_sequence=color_seq,
                            text="Complexity"
                        )
                        st.plotly_chart(fig_bar_complexity, use_container_width=True)

                    with col2:
                        fig_bar_violation = px.bar(
                            df,
                            x="Function",
                            y="Violations",
                            color="Function",
                            color_discrete_sequence=color_seq,
                            text="Violations"
                        )
                        st.plotly_chart(fig_bar_violation, use_container_width=True)

                    st.markdown("---")
                    st.markdown("### 🥧 Pie Chart Distribution")

                    col3, col4 = st.columns(2)

                    with col3:
                        fig_pie_complexity = px.pie(
                            df,
                            values="Complexity",
                            names="Function",
                            color_discrete_sequence=color_seq,
                            hole=0.4
                        )
                        st.plotly_chart(fig_pie_complexity, use_container_width=True)

                    with col4:
                        fig_pie_violation = px.pie(
                            df,
                            values="Violations",
                            names="Function",
                            color_discrete_sequence=color_seq,
                            hole=0.4
                        )
                        st.plotly_chart(fig_pie_violation, use_container_width=True)