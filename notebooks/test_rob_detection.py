import pandas as pd
from scraper.export_reader import load_latest_export

def test_rob_detection():
    print("Loading export...")
    reader = load_latest_export()
    
    print("Searching for RoB tables...")
    df_rob = reader.find_rob_tables()
    
    if df_rob.empty:
        print("No RoB tables found.")
    else:
        print(f"Found {len(df_rob)} RoB tables.")
        # Group by paper_id to see which papers have tables
        summary = df_rob.groupby('paper_id').size()
        print("\nSummary by paper:")
        print(summary)
        
        print("\nDetails of first few tables:")
        print(df_rob[['paper_id', 'section', 'matched_rob_refs']].head(10))

if __name__ == "__main__":
    test_rob_detection()
