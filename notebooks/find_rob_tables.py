# %% [markdown]
# # Find and Display Risk of Bias (RoB) Tables
# 
# This script demonstrates the enhanced `ExportReader` capabilities for identifying
# Risk of Bias tables using "smart search" based on references and citations.

# %% [markdown]
# ## Import Required Libraries

# %%
import pandas as pd
from pathlib import Path
from IPython.display import display, HTML

# Import the export reader library
from scraper.export_reader import load_latest_export

# %% [markdown]
# ## Load the Export Data

# %%
# Load the latest export
try:
    reader = load_latest_export()
    reader.print_summary()
except Exception as e:
    print(f"Error loading export: {e}")
    # Fallback or exit if no export found
    exit(1)

# %% [markdown]
# ## Smart Search for RoB Tables
# 
# Instead of searching for "method" or "risk of bias" in section titles, 
# we search for sections that cite foundational RoB literature (Higgins 2011, Sterne 2019).

# %%
print("=" * 80)
print("SMART SEARCH: FINDING TABLES BY CITATION")
print("=" * 80 + "\n")

# Use the new find_rob_tables method
df_rob_tables = reader.find_rob_tables()

if df_rob_tables.empty:
    print("❌ No RoB tables found using the smart search.")
    print("This might be because the papers don't cite the standard RoB tools,")
    print("or the citations weren't extracted correctly.")
else:
    print(f"✅ Found {len(df_rob_tables)} tables citing Risk of Bias tools!\n")
    display(df_rob_tables[['paper_id', 'section', 'matched_rob_refs', 'csv_path']])

# %% [markdown]
# ## Display Filtered Tables

# %%
def show_table(row_index, df_source):
    """Display a specific table from a given dataframe."""
    row = df_source.iloc[row_index]
    
    # Display metadata
    header = f"""
    <div style="background-color: #e8f4f8; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #2980b9;">
        <b>RoB Table #{row_index + 1}</b> | Paper: <b>{row['paper_id']}</b> | Section: <i>{row['section']}</i>
        <br>Matched References: {', '.join(row['matched_rob_refs'])}
    </div>
    """
    display(HTML(header))
    
    # Load and display the table
    try:
        df = reader.load_table_csv(row['csv_path'])
        display(df)
    except FileNotFoundError as e:
        print(f"❌ Error loading table: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    print("-" * 80)

# Display identified tables
if not df_rob_tables.empty:
    display_limit = min(10, len(df_rob_tables))
    print(f"Displaying top {display_limit} RoB tables...\n")
    
    for i in range(display_limit):
        try:
            show_table(i, df_rob_tables)
        except Exception as e:
            print(f"Error displaying table {i}: {e}")
            continue

# %% [markdown]
# ## Reference Inspection
# 
# Let's see what RoB references were found in the documents.

# %%
print("\n" + "=" * 80)
print("INSPECTING IDENTIFIED RoB REFERENCES")
print("=" * 80 + "\n")

df_refs = reader.get_all_references_dataframe()
if not df_refs.empty:
    # Filter for references that match our RoB criteria
    rob_dois = ['10.1136/bmj.d5928', '10.1136/bmj.l4898', 'd5928', 'l4898']
    rob_keywords = ['risk of bias', 'cochrane collaboration', 'rob 2', 'rob2']
    
    is_rob = df_refs['doi'].fillna('').str.lower().apply(
        lambda x: any(d.lower() in x for d in rob_dois)
    ) | df_refs['text'].fillna('').str.lower().apply(
        lambda x: any(k in x for k in rob_keywords)
    )
    
    found_rob_refs = df_refs[is_rob]
    print(f"Found {len(found_rob_refs)} unique RoB-related bibliographic entries across documents.")
    display(found_rob_refs[['paper_id', 'ref_id', 'doi', 'title', 'year']])
else:
    print("No references found in the export.")
