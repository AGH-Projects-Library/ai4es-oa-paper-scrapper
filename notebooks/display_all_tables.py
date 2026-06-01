# %% [markdown]
# # Display All Tables
# 
# This notebook loads the latest export and displays all tables in a loop with filtering options.

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
reader = load_latest_export()
reader.print_summary()

# Get all tables as a dataframe
df_tables = reader.get_all_tables_dataframe()
print(f"\n📊 Total tables to display: {len(df_tables)}\n")

# Display a preview
display(df_tables.head())

# %% [markdown]
# ## Display Tables in a Loop

# %%
def show_table(index):
    """Display a specific table from the tables dataframe."""
    if index < 0 or index >= len(df_tables):
        print('Index out of range')
        return
    
    row = df_tables.iloc[index]
    
    # Display metadata
    header = f"""
    <div style="background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
        <b>Table #{index + 1}</b> | Paper: {row['paper_id']} | Section: {row['section']} | Index: {row['table_index']}
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

# Display all tables in a loop
count = min(20, len(df_tables))
print(f"Starting to display {count} tables...\n")

for i in range(count):
    try:
        show_table(i)
    except Exception as e:
        print(f"Error displaying table {i}: {e}")
        continue

print(f"\n✅ Finished displaying all {count} tables!")

# %% [markdown]
# ## Filter and Display Specific Tables
# 
# Use the options below to display only specific tables based on various criteria.

# %%
# Filter 1: Tables in sections containing "method"
print("=" * 80)
print("FILTER 1: TABLES FROM 'METHOD' SECTIONS")
print("=" * 80 + "\n")

method_filter = df_tables[df_tables['section'].str.contains('method', case=False, na=False)]
print(f"Found {len(method_filter)} tables in sections containing 'method'\n")

display_limit = min(20, len(method_filter))
for idx, i in enumerate(method_filter.index[:display_limit]):
    try:
        print(f"\n[Method Filter - Table {idx + 1}/{display_limit}]")
        show_table(i)
    except Exception as e:
        print(f"Error displaying table {i}: {e}")
        continue

print(f"\n✅ Finished displaying {display_limit} tables from 'method' sections!")

# Filter 2: Tables in sections containing "risk of bias" or "rob" variations
print("\n\n" + "=" * 80)
print("FILTER 2: TABLES FROM 'RISK OF BIAS' / 'ROB' SECTIONS")
print("=" * 80 + "\n")

rob_filter = df_tables[
    df_tables['section'].str.contains('risk of bias|rob', case=False, na=False)
]
print(f"Found {len(rob_filter)} tables in sections containing 'risk of bias' or 'rob'\n")

display_limit = min(20, len(rob_filter))
for idx, i in enumerate(rob_filter.index[:display_limit]):
    try:
        print(f"\n[ROB Filter - Table {idx + 1}/{display_limit}]")
        show_table(i)
    except Exception as e:
        print(f"Error displaying table {i}: {e}")
        continue

print(f"\n✅ Finished displaying {display_limit} tables from 'risk of bias'/'rob' sections!")


# %% [markdown]
# ## Advanced Statistics

# %%
# Statistics about tables
print("📊 TABLE STATISTICS\n")
print(f"Total tables: {len(df_tables)}")
print(f"Unique papers: {df_tables['paper_id'].nunique()}")
print(f"Unique sections: {df_tables['section'].nunique()}\n")

print("Tables per section:")
section_counts = df_tables['section'].value_counts()
display(section_counts)

print("\nTables per paper (top 10):")
paper_counts = df_tables['paper_id'].value_counts().head(10)
display(paper_counts)


