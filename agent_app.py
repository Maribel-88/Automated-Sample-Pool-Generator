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

# --- 🌌 UNIFIED GLOBAL THEME OVERRIDES ---
st.markdown(
    """
    <style>
    .stApp { 
        background-color: #0b081a !important; 
    }
    h1, h2, h3, h4, h5, h6, label, p, span { 
        color: #f1ecff !important; 
    }
    
    /* Input field box accent boundaries */
    input[type="text"], .stNumberInput input {
        color: #ffffff !important; 
        background-color: #1b163d !important; 
        border: 1px solid #7d5bb5 !important; 
        font-weight: 600 !important;
    }
    
    /* 🔮 1. CORE DISPATCH TRIGGER BUTTON CLASS THEME */
    div.element-container button {
        background: linear-gradient(90deg, #311b92 0%, #6200ea 100%) !important; /* Deep Royal Purple */
        color: #ffffff !important; 
        font-weight: 700 !important;
        border: 1px solid #7c4dff !important;
        border-radius: 8px !important;
        height: 45px !important;
        box-shadow: 0 4px 12px rgba(98, 0, 234, 0.4) !important;
        transition: all 0.3s ease-in-out !important;
    }
    div.element-container button p {
        color: #ffffff !important;
    }
    div.element-container button:hover { 
        background: linear-gradient(90deg, #1a0c67 0%, #4a00b0 100%) !important;
        border-color: #b388ff !important;
        box-shadow: 0 6px 18px rgba(98, 0, 234, 0.7) !important;
    }
    
    /* 🎨 2. TARGET EXCEL EXPORT BUTTON SPECIFICS TO LIGHT GREEN */
    div[data-testid="stDownloadButton"] button {
        background: linear-gradient(90deg, #2e7d32 0%, #4caf50 100%) !important; /* Rich Light Green Gradient */
        border: 1px solid #81c784 !important;
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3) !important;
    }
    div[data-testid="stDownloadButton"] button:hover {
        background: linear-gradient(90deg, #1b5e20 0%, #388e3c 100%) !important;
        border-color: #a5d6a7 !important;
    }
    
    .summary-card {
        background-color: #19143a !important; border-left: 5px solid #00ffff !important; padding: 20px !important; border-radius: 12px !important; margin-bottom: 20px !important;
    }
    .labor-card {
        background-color: #1e1b4b !important; border: 2px solid #6366f1 !important; padding: 20px !important; border-radius: 12px !important; margin-bottom: 20px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📦 TeamLead AI: Warehouse Roster Dispatcher")
st.subheader("Automated Cross-Training & Labor Target Volume Planner")

if "warehouse_roster" not in st.session_state:
    st.session_state.warehouse_roster = generate_sample_warehouse_roster()
if "current_schedule" not in st.session_state:
    st.session_state.current_schedule = None

tab1, tab2 = st.tabs(["👥 100-Associate Team Matrix", "⚡ Daily Shift Task Allocation"])

# ================= TAB 1: RENDER THE MASTER POOL =================
with tab1:
    st.write("### Active Associate Training Matrix")
    st.write("All 100 associates are trained for Stowing. True checkboxes indicate verified advanced cross-training badges.")
    st.dataframe(st.session_state.warehouse_roster, width="stretch", height=400)
    
    st.write("### 📊 Skill Badge Inventory Summary")
    skill_counts = st.session_state.warehouse_roster.drop(columns=["Current_Assignment"]).sum()
    st.bar_chart(skill_counts)

# ================= TAB 2: INTAKE TARGETS & RESULTS RUN =================
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
    st.write("### ⚡ Step 2: Configure Indirect Process Headcounts")
    
    # 🌟 REMOVED THE CONFLICTING ST.FORM WRAPPER ENTIRELY
    col1, col2, col3 = st.columns(3)
    with col1:
        req_cubi_pick = st.number_input("Cubiscan Picking Staff (Max 5):", min_value=0, max_value=5, value=2)
        req_pal_stow = st.number_input("Pallet Stower Staff (Max 5):", min_value=0, max_value=5, value=2)
        req_instructor = st.number_input("Instructors (Max 5):", min_value=0, max_value=5, value=1)
        req_prep = st.number_input("Prep Staff (Max 8):", min_value=0, max_value=8, value=3)
    with col2:
        req_puller = st.number_input("Pallet Puller Staff (Max 8):", min_value=0, max_value=8, value=3)
        req_cubiscan = st.number_input("Cubiscan Staff (Max 10):", min_value=0, max_value=10, value=4)
        req_cart = st.number_input("Cart Builder Staff (Max 10):", min_value=0, max_value=10, value=5)
    with col3:
        req_decant = st.number_input("Decant Staff (Max 15):", min_value=0, max_value=15, value=6)
        req_receive = st.number_input("Receive Staff (Max 20):", min_value=0, max_value=20, value=10)
        
        allocated_indirects = req_cubi_pick + req_pal_stow + req_instructor + req_prep + req_puller + req_cubiscan + req_cart + req_decant + req_receive
        max_picking_headroom = max(0, 100 - allocated_indirects)
        
        if needed_stowers + allocated_indirects < 100:
            recommended_picking = 100 - needed_stowers - allocated_indirects
        else:
            recommended_picking = 0
            
        req_picking = st.number_input(f"Picking Staff (Max {max_picking_headroom}):", min_value=0, max_value=max_picking_headroom, value=min(recommended_picking, 30))
        
    st.write("")
       # 🔮 STANDARD NATIVE BUTTON LAYER - BYPASSES SHADOW DOM COMPILATION LOCKS
    submit_allocations = st.button("Optimize Workload Allocations Matrix 🚀", use_container_width=True)
        
    if submit_allocations:
        shift_targets = {
            "Cubiscan Picking": req_cubi_pick, "Pallet Stower": req_pal_stow,
            "Instructor": req_instructor, "Prep": req_prep, "Pallet Puller": req_puller,
            "Cubiscan": req_cubiscan, "Cart Builder": req_cart, "Decant": req_decant,
            "Receive": req_receive, "Picking": req_picking
        }
        
        with st.spinner("Executing scarcity-first routing logic arrays..."):
            optimized_schedule = allocate_shift_tasks(st.session_state.warehouse_roster, shift_targets)
            st.session_state.current_schedule = optimized_schedule
        st.success("✅ Shift Assignment Schedule Generated Instantly!")

    # If an optimization run exists, render the live dispatch results
    if st.session_state.current_schedule is not None:
        st.divider()
        st.write("### 🔮 Optimized Live Dispatch Schedule")
        
        stow_count = int((st.session_state.current_schedule["Current_Assignment"] == "Stowing").sum())
        surplus_associates = stow_count - needed_stowers
        
        grouped_tasks = {}
        for associate_id, row in st.session_state.current_schedule.iterrows():
            assignment = row["Current_Assignment"]
            if assignment not in grouped_tasks:
                grouped_tasks[assignment] = []
            grouped_tasks[assignment].append(associate_id)
        
        if surplus_associates > 0:
            if "Picking" in vto_action:
                surplus_to_move = min(surplus_associates, 30 - req_picking)
                if surplus_to_move > 0:
                    st.warning(f"⚠️ Labor Surplus Detected: You have {surplus_associates} extra Stowers over your target capacity. Strategy Triggered: Reallocating **{surplus_to_move} cross-trained Stowers** straight to the **Picking Department** queue.")
                    for _ in range(surplus_to_move):
                        if grouped_tasks.get("Stowing"):
                            name = grouped_tasks["Stowing"].pop()
                            if "Picking" not in grouped_tasks: 
                                grouped_tasks["Picking"] = []
                            grouped_tasks["Picking"].append(name)
                    stow_count -= surplus_to_move
            else:
                st.info(f"🛑 Labor Surplus Detected: Target volume requires {needed_stowers} Stowers, but you have {stow_count} scheduled. Strategy Triggered: Flagging **{surplus_associates} associates** for **Voluntary Time Off (VTO)** options.")
                if "VTO Eligible / Standby" not in grouped_tasks:
                    grouped_tasks["VTO Eligible / Standby"] = []
                for _ in range(surplus_associates):
                    if grouped_tasks.get("Stowing"):
                        name = grouped_tasks["Stowing"].pop()
                        grouped_tasks["VTO Eligible / Standby"].append(name)
                stow_count -= surplus_associates

        max_len = max(len(associates) for associates in grouped_tasks.values()) if grouped_tasks else 0
        balanced_columns = {}
        for task, associates in grouped_tasks.items():
            balanced_columns[task] = associates + [""] * (max_len - len(associates))

        task_directory_df = pd.DataFrame(balanced_columns)

        sum_col, btn_col = st.columns(2)
        with sum_col:
            st.markdown(
                f"""
                <div class="summary-card" style="margin-bottom:0;">
                    <h4 style='margin:0 0 5px 0; color:#00ffff !important;'>📋 SHIFT DEPLOYVIEW OVERVIEW</h4>
                    <p style='margin:0; color:#ffffff !important;'><b>100 Associates</b> successfully routed. 
                    Target volume balanced. <b>{stow_count} Associates</b> locked onto active <b>Stowing lines</b>.</p>
                </div>
                """,
                unsafe_allow_html=True
            )
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
            final_flat_list = []
            for t, names in grouped_tasks.items():
                for name in names:
                    if name != "": 
                        final_flat_list.append(t)
            
            chart_data = pd.DataFrame({"Task": final_flat_list}).value_counts().reset_index(name="Associate Headcount")
            st.bar_chart(data=chart_data, x="Task", y="Associate Headcount")

st.divider()
st.caption("Powered by Google Gemini 3.8 Flash & Your Custom Shift Supervisor Local Engine.")
