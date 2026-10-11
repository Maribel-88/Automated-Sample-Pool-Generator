# roster_engine.py
import random
import pandas as pd
import io

def generate_sample_warehouse_roster() -> pd.DataFrame:
    """Generates a sample dataset of 100 associates with cross-training frequencies."""
    random.seed(42) # Keeps names and allocation maps consistent across page reloads
    
    total_associates = 100
    
    # Create the 100 base associates - ALL are automatically trained for Stowing
    roster = {
        f"Associate {str(i).zfill(3)}": {
            "Stowing": True, "Picking": False, "Cubiscan": False, 
            "Cubiscan Picking": False, "Decant": False, "Receive": False, 
            "Prep": False, "Pallet Puller": False, "Pallet Stower": False, 
            "Cart Builder": False, "Instructor": False, "Current_Assignment": "Stowing"
        } for i in range(1, total_associates + 1)
    }
    
    associate_keys = list(roster.keys())
    
    # Helper distribution engine to cleanly overlay cross-training parameters
    def apply_cross_training(task_name: str, count: int):
        random.shuffle(associate_keys)
        for key in associate_keys[:count]:
            roster[key][task_name] = True

    # Overlay your exact required training numbers across the 100 stowers
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
    
    df = pd.DataFrame.from_dict(roster, orient='index')
    return df

def allocate_shift_tasks(roster_df: pd.DataFrame, targets: dict) -> pd.DataFrame:
    """
    Executes a scarcity-first priority matching algorithm.
    Allocates cross-trained personnel to rare processes first, 
    and defaults the remaining associates to Stowing.
    """
    working_df = roster_df.copy()
    working_df["Current_Assignment"] = "Unassigned"
    
    priority_order = [
        "Cubiscan Picking", "Pallet Stower", "Instructor", 
        "Prep", "Pallet Puller", "Cubiscan", "Cart Builder", 
        "Decant", "Receive", "Picking"
    ]
    
    assigned_associates = set()
    
    for task in priority_order:
        needed_count = targets.get(task, 0)
        if needed_count <= 0:
            continue
            
        allocated_to_task = 0
        
        for associate_id, row in working_df.iterrows():
            if allocated_to_task >= needed_count:
                break
                
            if associate_id not in assigned_associates and row[task] == True:
                working_df.at[associate_id, "Current_Assignment"] = task
                assigned_associates.add(associate_id)
                allocated_to_task += 1
                
    for associate_id in working_df.index:
        if associate_id not in assigned_associates:
            working_df.at[associate_id, "Current_Assignment"] = "Stowing"
            
    return working_df

def convert_df_to_excel(df: pd.DataFrame) -> bytes:
    """Converts a DataFrame into raw Excel binary bytes for download tracking."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Shift_Assignments')
    return output.getvalue()
