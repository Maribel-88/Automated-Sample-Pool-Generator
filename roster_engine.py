# roster_engine.py
import random
import pandas as pd
import io
from datetime import datetime

def generate_sample_warehouse_roster() -> pd.DataFrame:
    """Generates a sample dataset of 100 associates with cross-training frequencies."""
    random.seed(42)
    total_associates = 100
    roster = {
        f"Associate {str(i).zfill(3)}": {
            "Stowing": True, "Picking": False, "Cubiscan": False, 
            "Cubiscan Picking": False, "Decant": False, "Receive": False, 
            "Prep": False, "Pallet Puller": False, "Pallet Stower": False, 
            "Cart Builder": False, "Instructor": False, "Current_Assignment": "Stowing"
        } for i in range(1, total_associates + 1)
    }
    associate_keys = list(roster.keys())
    
    def apply_cross_training(task_name: str, count: int):
        random.shuffle(associate_keys)
        for key in associate_keys[:count]:
            roster[key][task_name] = True

    apply_cross_training("Picking", 30)
    apply_cross_training("Cubiscan", 10)
    apply_cross_training("Cubiscan Picking", 5)
    apply_cross_training("Decant", 15)
    apply_cross_training("Receive", 20)
    apply_cross_training("Prep", 8)
    apply_cross_training("Pallet Puller", 8)
    apply_cross_training("Pallet Stower", 5)
    apply_cross_training("Cart Builder", 10)
    apply_cross_training("Instructor", 5)
    
    return pd.DataFrame.from_dict(roster, orient='index')

def allocate_shift_tasks(roster_df: pd.DataFrame, targets: dict, blocklist_dict: dict = None) -> pd.DataFrame:
    """
    Executes a scarcity-first priority matching algorithm.
    🌟 INTEGRATES 2-DAY CONSECUTIVE ASSIGNMENT ROTATION BLOCKS VIA BLOCKLIST_DICT!
    """
    working_df = roster_df.copy()
    working_df["Current_Assignment"] = "Unassigned"
    
    if blocklist_dict is None:
        blocklist_dict = {}
    
    priority_order = [
        "Cubiscan Picking", "Pallet Stower", "Instructor", 
        "Prep", "Pallet Puller", "Cubiscan", "Cart Builder", 
        "Decant", "Receive", "Picking"
    ]
    
    assigned_associates = set()
    today_seed = int(datetime.now().strftime("%Y%m%d"))
    
    rotated_associate_ids = list(working_df.index)
    random.seed(today_seed)
    random.shuffle(rotated_associate_ids)
    
    for task in priority_order:
        needed_count = targets.get(task, 0)
        if needed_count <= 0:
            continue
            
        allocated_to_task = 0
        
        for associate_id in rotated_associate_ids:
            if allocated_to_task >= needed_count:
                break
                
            # Check if this specific associate is strictly blocklisted from this task today
            is_blocklisted = associate_id in blocklist_dict and blocklist_dict[associate_id] == task
            
            if (associate_id not in assigned_associates and 
                working_df.at[associate_id, task] == True and 
                not is_blocklisted):
                
                working_df.at[associate_id, "Current_Assignment"] = task
                assigned_associates.add(associate_id)
                allocated_to_task += 1
                
    # Standard Stowing fallback lane handles the rest
    for associate_id in working_df.index:
        if associate_id not in assigned_associates:
            working_df.at[associate_id, "Current_Assignment"] = "Stowing"
            
    return working_df

def convert_df_to_excel(df: pd.DataFrame) -> bytes:
    """Converts a pivoted DataFrame into raw Excel binary bytes with safe column width auto-fitting."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Shift_Directory')
        worksheet = writer.sheets['Shift_Directory']
        
        for col_idx, col_name in enumerate(df.columns, start=1):
            max_len = max(df[col_name].astype(str).map(len).max(), len(str(col_name)))
            if col_idx <= 26:
                col_letter = chr(64 + col_idx)
            else:
                col_letter = chr(64 + (col_idx // 26)) + chr(64 + (col_idx % 26))
                
            worksheet.column_dimensions[col_letter].width = max(max_len + 3, 15)
            
    return output.getvalue()
