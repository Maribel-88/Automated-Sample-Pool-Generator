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

# --- 🌌 STYLING OVERRIDES FOR PROFESSIONAL VISIBILITY ---
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
    button[data-testid="baseButton-formSubmit"] {
        background: linear-gradient(90deg, #4b1a8a 0%, #6622cc 100%) !important; color: #ffffff !important; font-weight: bold !important;
    }
    button[data-testid="baseButton-formSubmit"]:hover { box-shadow: 0 0 15px rgba(179, 136, 255, 0.7) !important; }
    
    .summary-card {
        background-color: #19143a !important; border-left: 5px solid #00ffff !important; padding: 20px !important; border-radius: 12px !important; margin-bottom: 20px !important;
    }
    /* 🌟 Labor Strategy Alert Box Styles */
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
    st.write("Input today's processing volumes to calculate target headcounts based on standard operational rates (180 units/hr for 10 hours).")
    
    # 🌟 NEW ELEMENT: LIVE INVENTORY CALCULATOR
    st_col1, st_col2 = st.columns(2)
    with st_col1:
        target_stow_volume = st.number_input("Target Stow Inventory Volume (Units):", min_value=0, max_value=200000, value=90000, step=5000)
    with st_col2:
        vto_action = st.radio("Surplus Labor Action Strategy:", options=["Prioritise Picking Department Reallocation 📊", "Raise VTO (Voluntary Time Off) 🛑"], index=0)
    
    # Run Labor Operational Math
    stower_rate_per_day = 180 * 10 # 1,800 units per shift per person
    needed_stowers = math.ceil(target_stow_volume / stower_rate_per_day)
    available_pool = 100
    
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
    st.write("Specify your indirect workflow requirements. The engine will automatically distribute the remaining cross-trained staff.")
    
    with st.form("shift_targets_form"):
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
            
            # The remaining pool is dynamically calculated
            allocated_indirects = req_cubi_pick + req_pal_stow + req_instructor + req_prep + req_puller + req_cubiscan + req_cart + req_decant + req_receive
            max_picking_headroom = max(0, 100 - allocated_indirects)
            
            # Handle the Picking distribution based on user's target volume constraints
            if needed_stowers + allocated_indirects < 100:
                recommended_picking = 100 - needed_stowers - allocated_indirects
            else:
                recommended_picking = 0
                
            req_picking = st.number_input(f"Picking Staff (Max {max_picking_headroom}):", min_value=0, max_value=max_picking_headroom, value=min(recommended_picking, 30))
            
        submit_allocations = st.form_submit_button("Optimize Workload Allocations Matrix 🚀", width="stretch")
        
    if submit_allocations:
        total_requested = (req_picking + req_cubiscan + req_cubi_pick + req_decant + 
                           req_receive + req_prep + req_puller + req_pal_stow + req_cart + req_instructor)
        
        if total_requested > 100:
            st.error(f"❌ Allocation Plan Rejected: You requested {total_requested} associates, but your total roster maximum is 100!")
        else:
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
        
        # Calculate surplus parameters dynamically
        surplus_associates = stow_count - needed_stowers
        
        # Group and pivot data columns
        grouped_tasks = {}
        for associate_id, row in st.session_state.current_schedule.iterrows():
            assignment = row["Current_Assignment"]
            if assignment not in grouped_tasks:
                grouped_tasks[assignment] = []
            grouped_tasks[assignment].append(associate_id)
        
                # Handle labor balance output notifications if people exceed the required target count
        if surplus_associates > 0:
            if "Picking" in vto_action:
                # Action: Reallocate surplus Stowers directly to the Picking department field
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
                # Action: Flag them for Voluntary Time Off (VTO)
                st.info(f"🛑 Labor Surplus Detected: Target volume requires {needed_stowers} Stowers, but you have {stow_count} scheduled. Strategy Triggered: Flagging **{surplus_associates} associates** for **Voluntary Time Off (VTO)** options.")
                if "VTO Eligible / Standby" not in grouped_tasks:
                    grouped_tasks["VTO Eligible / Standby"] = []
                for _ in range(surplus_associates):
                    if grouped_tasks.get("Stowing"):
                        name = grouped_tasks["Stowing"].pop()
                        grouped_tasks["VTO Eligible / Standby"].append(name)
                stow_count -= surplus_associates

        # Pad shorter columns with empty spaces so they align perfectly into a grid matrix
        max_len = max(len(associates) for associates in grouped_tasks.values()) if grouped_tasks else 0
        balanced_columns = {}
        for task, associates in grouped_tasks.items():
            balanced_columns[task] = associates + [""] * (max_len - len(associates))

        task_directory_df = pd.DataFrame(balanced_columns)

        # RENDER SUMMARY OVERVIEW CARD WITH INTEGRATED DOWNLOAD TRIGGER HUB
        sum_col, btn_col = st.columns(2)
        with sum_col:
            st.markdown(
                f"""
                <div class="summary-card" style="margin-bottom:0;">
                    <h4 style='margin:0 0 5px 0; color:#00ffff !important;'>📋 SHIFT DEPLOYMENT OVERVIEW</h4>
                    <p style='margin:0; color:#ffffff !important;'><b>100 Associates</b> successfully routed. 
                    Target volume balanced. <b>{stow_count} Associates</b> locked onto active **Stowing lines**.</p>
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
            # Recalculate counts accurately based on the shifted data categories
            final_flat_list = []
            for t, names in grouped_tasks.items():
                for name in names:
                    if name != "": 
                        final_flat_list.append(t)
            
            # Render a vertical column bar chart indexed explicitly by Task headings
            chart_data = pd.DataFrame({"Task": final_flat_list}).value_counts().reset_index(name="Associate Headcount")
            st.bar_chart(data=chart_data, x="Task", y="Associate Headcount")

st.divider()
st.caption("Powered by Google Gemini 3.8 Flash & Your Custom Shift Supervisor Local Engine.")
