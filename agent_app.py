# agent_app.py
import streamlit as st
import pandas as pd
import math
from datetime import datetime
from roster_engine import generate_sample_warehouse_roster, allocate_shift_tasks, convert_df_to_excel

st.set_page_config(
    page_title="TeamLead AI - Warehouse Roster Agent",
    page_icon="📦",
    layout="wide"
)

# --- 🌌 GLOBAL THEME OVERRIDES ---
st.markdown(
    """
    <style>
    .stApp { background-color: #0b081a !important; }
    h1, h2, h3, h4, h5, h6, label, p, span { color: #f1ecff !important; }
    [data-testid="stForm"] {
        background-color: #120e2b !important; border: 2px solid #5a3d96 !important; border-radius: 12px !important; padding: 20px !important;
    }
    input[type="text"], .stNumberInput input {
        color: #ffffff !important; background-color: #1b163d !important; border: 1px solid #7d5bb5 !important; font-weight: 600 !important;
    }
    div.element-container button {
        background: linear-gradient(90deg, #311b92 0%, #6200ea 100%) !important;
        color: #ffffff !important; font-weight: 700 !important; border: 1px solid #7c4dff !important; border-radius: 8px !important; height: 45px !important;
        box-shadow: 0 4px 12px rgba(98, 0, 234, 0.4) !important; transition: all 0.3s ease-in-out !important;
    }
    div.element-container button p, div.element-container button span { color: #ffffff !important; }
    div.element-container button:hover { background: linear-gradient(90deg, #1a0c67 0%, #4a00b0 100%) !important; border-color: #b388ff !important; box-shadow: 0 6px 18px rgba(98, 0, 234, 0.7) !important; transform: translateY(-1px) !important; }
    div[data-testid="stDownloadButton"] button { background: linear-gradient(90deg, #2e7d32 0%, #4caf50 100%) !important; border: 1px solid #81c784 !important; box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3) !important; }
    div[data-testid="stDownloadButton"] button:hover { background: linear-gradient(90deg, #1b5e20 0%, #388e3c 100%) !important; border-color: #a5d6a7 !important; box-shadow: 0 6px 18px rgba(76, 175, 80, 0.6) !important; }
    .summary-card { background-color: #19143a !important; border-left: 5px solid #00ffff !important; padding: 20px !important; border-radius: 12px !important; margin-bottom: 20px !important; }
    .labor-card { background-color: #1e1b4b !important; border: 2px solid #6366f1 !important; padding: 20px !important; border-radius: 12px !important; margin-bottom: 20px !important; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📦 TeamLead AI: Warehouse Roster Dispatcher")
st.subheader("Automated Cross-Training & 2-Day Consecutive Task Rotation Guard")

if "warehouse_roster" not in st.session_state:
    st.session_state.warehouse_roster = generate_sample_warehouse_roster()
if "current_schedule" not in st.session_state:
    st.session_state.current_schedule = None

if "targets" not in st.session_state:
    st.session_state.targets = {
        "Cubiscan Picking": 2, "Pallet Stower": 2, "Instructor": 1, "Prep": 3,
        "Pallet Puller": 3, "Cubiscan": 4, "Cart Builder": 5, "Decant": 6,
        "Receive": 10, "Picking": 12
    }

tab1, tab2 = st.tabs(["👥 100-Associate Team Matrix", "⚡ Daily Shift Task Allocation"])

# ================= TAB 1 =================
with tab1:
    st.write("### Active Associate Training Matrix")
    st.dataframe(st.session_state.warehouse_roster, width="stretch", height=400)
    skill_counts = st.session_state.warehouse_roster.drop(columns=["Current_Assignment"]).sum()
    st.bar_chart(skill_counts)

# ================= TAB 2 =================
with tab2:
    st.write("### 📊 Step 1: Shift Target Inventory Volume Planner")
    st_col1, st_col2 = st.columns(2)
    with st_col1:
        target_stow_volume = st.number_input("Target Stow Inventory Volume (Units):", min_value=0, max_value=200000, value=90000, step=5000)
    with st_col2:
        vto_action = st.radio("Surplus Labor Action Strategy:", options=["Prioritise Picking Department Reallocation 📊", "Raise VTO (Voluntary Time Off) 🛑"], index=0)
    
    stower_rate_per_day = 180 * 10
    needed_stowers = math.ceil(target_stow_volume / stower_rate_per_day)
    
    st.markdown(
        f"""
        <div class="labor-card">
            <h4 style='margin:0 0 8px 0; color:#a5b4fc !important;'>💡 OPERATIONAL LABOR PLANNING INSIGHT</h4>
            <p style='margin:0 0 5px 0;'>At 180 units/hr over a 10-hour shift, each associate can process <b>{stower_rate_per_day:,} units</b>.</p>
            <p style='margin:0;'>To hit your <b>{target_stow_volume:,} units</b> target today, you need exactly: <b style='color:#00ffff;'>{needed_stowers} Stowers</b>.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.divider()
    
    # 🌟 NEW ELEMENT: HISTORICAL UPLOAD ROTATION BLOCKED DRAWER
    st.write("### ⏳ Step 2: 2-Day Consecutive Task Rotation Safety Gate (Optional)")
    st.write("To prevent associates from doing the same indirect task for more than 2 consecutive days, drop yesterday's and the day before yesterday's exported shift Excel files below.")
    
    hist_col1, hist_col2 = st.columns(2)
    blocklist = {}
    
    with hist_col1:
        file_day1 = st.file_uploader("Upload Yesterday's Exported Schedule (Day -1):", type=["xlsx"], key="hist_day_1")
    with hist_col2:
        file_day2 = st.file_uploader("Upload Day Before Yesterday's Schedule (Day -2):", type=["xlsx"], key="hist_day_2")
        
    if file_day1 and file_day2:
        try:
            df_day1 = pd.read_excel(file_day1)
            df_day2 = pd.read_excel(file_day2)
            
            # Extract historical paths by reverse-pivoting column arrays back to flat metrics rows
            history_maps = {}
            for df in [df_day1, df_day2]:
                for task_col in df.columns:
                    # Ignore VTO standby pools from the rotation constraints limits
                    if "VTO" in task_col:
                        continue
                    for worker in df[task_col].dropna().astype(str):
                        if worker.strip() and "Associate" in worker:
                            if worker not in history_maps: 
                                history_maps[worker] = []
                            history_maps[worker].append(task_col)
            
            # Identify associates who worked the identical indirect task on BOTH days
            for worker, tasks in history_maps.items():
                if len(tasks) >= 2 and tasks[0] == tasks[1] and tasks[0] != "Stowing":
                    blocklist[worker] = tasks[0]
            
            if blocklist:
                st.warning(f"⚠️ Rotation Guard Activated: Found **{len(blocklist)} associates** who worked the exact same indirect process for 2 consecutive days. They will be strictly blocked from those specific assignments today!")
            else:
                st.success("✅ Rotation Check Passed: No associates have exceeded consecutive task limits.")
        except Exception as e:
            st.error(f"❌ Error compiling history streams: Verify Excel structure format matches default exports. Details: {e}")

    st.divider()
    st.write("### ⚡ Step 3: Configure & Run Headcount Allocation Matrix")
    
    with st.form("shift_targets_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            req_cubi_pick = st.number_input("Cubiscan Picking Staff:", min_value=0, max_value=5, value=int(st.session_state.targets["Cubiscan Picking"]))
            req_pal_stow = st.number_input("Pallet Stower Staff:", min_value=0, max_value=5, value=int(st.session_state.targets["Pallet Stower"]))
            req_instructor = st.number_input("Instructors:", min_value=0, max_value=5, value=int(st.session_state.targets["Instructor"]))
            req_prep = st.number_input("Prep Staff:", min_value=0, max_value=8, value=int(st.session_state.targets["Prep"]))
        with col2:
            req_puller = st.number_input("Pallet Puller Staff:", min_value=0, max_value=8, value=int(st.session_state.targets["Pallet Puller"]))
            req_cubiscan = st.number_input("Cubiscan Staff:", min_value=0, max_value=10, value=int(st.session_state.targets["Cubiscan"]))
            req_cart = st.number_input("Cart Builder Staff:", min_value=0, max_value=10, value=int(st.session_state.targets["Cart Builder"]))
        with col3:
            req_decant = st.number_input("Decant Staff:", min_value=0, max_value=15, value=int(st.session_state.targets["Decant"]))
            req_receive = st.number_input("Receive Staff:", min_value=0, max_value=20, value=int(st.session_state.targets["Receive"]))
            
            allocated_indirects = req_cubi_pick + req_pal_stow + req_instructor + req_prep + req_puller + req_cubiscan + req_cart + req_decant + req_receive
            max_picking_headroom = max(0, 100 - allocated_indirects)
            recommended_picking = max(0, 100 - needed_stowers - allocated_indirects) if needed_stowers + allocated_indirects < 100 else 0
            
            req_picking = st.number_input(f"Picking Staff (Max {max_picking_headroom}):", min_value=0, max_value=max_picking_headroom, value=min(recommended_picking, int(st.session_state.targets["Picking"])))
            
        submit_allocations = st.form_submit_button("Optimize Workload Allocations Matrix 🚀", width="stretch")

    if submit_allocations:
        st.session_state.targets = {
            "Cubiscan Picking": req_cubi_pick, "Pallet Stower": req_pal_stow, "Instructor": req_instructor,
            "Prep": req_prep, "Pallet Puller": req_puller, "Cubiscan": req_cubiscan,
            "Cart Builder": req_cart, "Decant": req_decant, "Receive": req_receive, "Picking": req_picking
        }
        with st.spinner("Executing scarcity-first routing logic arrays..."):
            st.session_state.current_schedule = allocate_shift_tasks(st.session_state.warehouse_roster, st.session_state.targets, blocklist_dict=blocklist)
        st.success("✅ Shift Assignment Schedule Generated Instantly!")

    if st.session_state.current_schedule is not None:
        st.divider()
        st.write("### 🔮 Optimized Live Dispatch Schedule")
        
        # 🔍 Live Associate Assignment Finder
        search_query = st.text_input("Quick-Search Associate Assignment:", placeholder="Type Name or ID number...").strip()
        
        if search_query:
            matched = [idx for idx in st.session_state.current_schedule.index if search_query.lower() in idx.lower()]
            if matched:
                for associate in matched:
                    assigned_job = st.session_state.current_schedule.at[associate, "Current_Assignment"]
                    if assigned_job == "Stowing": st.info(f"📋 **{associate}** is on active **STOWING** lines.")
                    elif assigned_job == "Picking": st.warning(f"📊 **{associate}** is routed to **PICKING**.")
                    elif "VTO" in assigned_job: st.error(f"🛑 **{associate}** is flagged for **VTO STANDBY**.")
                    else: st.success(f"✨ **{associate}** is on **{assigned_job.upper()}**.")
                    
                    with st.expander(f"⚙️ Reallocate / Change Task for {associate}"):
                        new_job = st.selectbox(f"Select New Task:", options=["Stowing", "Picking", "Cubiscan", "Decant", "Receive", "Prep"], key=f"reassign_{associate}")
                        if st.button(f"Confirm Override ⚡", key=f"btn_{associate}", use_container_width=True):
                            st.session_state.current_schedule.at[associate, "Current_Assignment"] = new_job
                            st.rerun()
            else: 
                st.error("❌ No matching associate found.")

        stow_count = int((st.session_state.current_schedule["Current_Assignment"] == "Stowing").sum())
        surplus_associates = stow_count - needed_stowers
        grouped_tasks = {}
        for associate_id, row in st.session_state.current_schedule.iterrows():
            assignment = row["Current_Assignment"]
            if assignment not in grouped_tasks: 
                grouped_tasks[assignment] = []
            grouped_tasks[assignment].append(associate_id)
            
        if surplus_associates > 0:
            if vto_action == "Prioritise Picking Department Reallocation 📊":
                surplus_to_move = min(surplus_associates, 30 - req_picking)
                for _ in range(surplus_to_move):
                    if grouped_tasks.get("Stowing") and len(grouped_tasks["Stowing"]) > 0:
                        if "Picking" not in grouped_tasks: 
                            grouped_tasks["Picking"] = []
                        grouped_tasks["Picking"].append(grouped_tasks["Stowing"].pop())
                stow_count -= surplus_to_move
            elif vto_action == "Raise VTO (Voluntary Time Off) 🛑":
                if "VTO Eligible / Standby" not in grouped_tasks: 
                    grouped_tasks["VTO Eligible / Standby"] = []
                for _ in range(surplus_associates):
                    if grouped_tasks.get("Stowing") and len(grouped_tasks["Stowing"]) > 0: 
                        grouped_tasks["VTO Eligible / Standby"].append(grouped_tasks["Stowing"].pop())
                stow_count -= surplus_associates

        max_len = max(len(associates) for associates in grouped_tasks.values()) if grouped_tasks else 0
        balanced_columns = {t: acc + [""] * (max_len - len(acc)) for t, acc in grouped_tasks.items()}
        task_directory_df = pd.DataFrame(balanced_columns)

        sum_col, btn_col = st.columns(2)
        with sum_col: 
            st.markdown(f'<div class="summary-card"><h4>📋 SHIFT DEPLOYMENT OVERVIEW</h4><p><b>100 Associates</b> successfully routed. Target volume balanced. <b>{stow_count} Associates</b> locked onto active <b>Stowing lines</b>.</p></div>', unsafe_allow_html=True)
        with btn_col:
            st.write("#### ")
            excel_bytes = convert_df_to_excel(task_directory_df)
            st.download_button(
                label="Export Schedule to Excel 📊", 
                data=excel_bytes, 
                file_name=f"Warehouse_Shift_Schedule_{datetime.now().strftime('%d-%m-%Y')}.xlsx", 
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                width="stretch"
            )
        
        st.write("")
        
        c1, c2 = st.columns(2)
        with c1:
            st.write("#### 👤 Task Assignment Directory")
            st.dataframe(task_directory_df, width="stretch", height=400)
        with c2:
            st.write("#### 📊 Final Shift Headcount Deployment")
            final_flat_list = [t for t, names in grouped_tasks.items() for name in names if name != ""]
            chart_data = pd.DataFrame({"Task": final_flat_list}).value_counts().reset_index(name="Associate Headcount")
            st.bar_chart(data=chart_data, x="Task", y="Associate Headcount")

st.divider()
st.caption("Powered by Your Custom Shift Supervisor Local Engine.")
