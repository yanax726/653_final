#!/usr/bin/env python3

import pandas as pd
import re
from pathlib import Path

dct_file = Path("data/ECLSK2011_K5PUF.dct")

# Variables we MUST extract for the analysis
REQUIRED_VARS = [
    # === FOOD SECURITY (PRIMARY PREDICTOR) ===
    "X1FSRAW", "X2FSRAW", "X4FSRAW", "X6FSRAW", "X7FSRAW", "X8FSRAW", "X9FSRAW",
    "X1FSCMBI", "X2FSCMBI", "X4FSCMBI", "X6FSCMBI", "X7FSCMBI", "X8FSCMBI", "X9FSCMBI",
    
    # === READING SCORES (OUTCOME) ===
    "X1RSCALK5", "X2RSCALK5", "X3RSCALK5", "X4RSCALK5", "X5RSCALK5",
    "X6RSCALK5", "X7RSCALK5", "X8RSCALK5", "X9RSCALK5",
    
    # === TEACHER-RATED SOCIAL-EMOTIONAL (OUTCOME) ===
    # Self-control
    "X1TCHCON", "X2TCHCON", "X4TCHCON", "X6TCHCON", "X7TCHCON", "X8TCHCON", "X9TCHCON",
    # Approaches to learning
    "X1TCHAPP", "X2TCHAPP", "X4TCHAPP", "X6TCHAPP", "X7TCHAPP", "X8TCHAPP", "X9TCHAPP",
    # Externalizing behaviors
    "X1TCHEXT", "X2TCHEXT", "X4TCHEXT", "X6TCHEXT", "X7TCHEXT", "X8TCHEXT", "X9TCHEXT",
    # Internalizing behaviors
    "X1TCHINT", "X2TCHINT", "X4TCHINT", "X6TCHINT", "X7TCHINT", "X8TCHINT", "X9TCHINT",
    
    # === MISSING CONTROL VARIABLES ===
    "X_RACETH_R", "X1KAGE", "X1FIRKDG", "X2FIRKDG",
    "X1HPARNT", "X2HPARNT", "X4HPARNT",
    
    # === SAMPLING WEIGHTS ===
    "W1C0", "W2C0", "W3C0", "W4C0", "W5C0", "W6C0", "W7C0", "W8C0", "W9C0",
    
    # === ALSO NEED CHILDID TO MERGE ===
    "CHILDID"
]

print(f"Variables to extract: {len(REQUIRED_VARS)}")
print()

# Parse .dct file
var_specs = []
current_line_num = 1

with open(dct_file, 'r', encoding='latin-1', errors='replace') as f:
    for line in f:
        # Track which line within the 27-line record
        if '_line(' in line:
            match = re.search(r'_line\((\d+)\)', line)
            if match:
                current_line_num = int(match.group(1))
        
        # Parse variable specifications
        if '_column(' in line:
            # Extract column position
            col_match = re.search(r'_column\((\d+)\)', line)
            if col_match:
                col_pos = int(col_match.group(1))
                
                # Extract type and variable name
                parts = line.split()
                col_idx = next((i for i, p in enumerate(parts) if '_column' in p), None)
                
                if col_idx is not None and len(parts) > col_idx + 2:
                    var_type = parts[col_idx + 1]
                    var_name = parts[col_idx + 2]
                    
                    # Determine width based on type
                    if var_type.startswith('str'):
                        width = int(var_type[3:])
                        dtype = 'str'
                    elif var_type in ['byte', 'int', 'long']:
                        width = 7
                        dtype = 'int'
                    elif var_type in ['float', 'double']:
                        width = 11
                        dtype = 'float'
                    else:
                        width = 10
                        dtype = 'str'
                    
                    # Only keep variables we need
                    if var_name.upper() in REQUIRED_VARS:
                        var_specs.append({
                            'name': var_name.upper(),
                            'line': current_line_num,
                            'col': col_pos,
                            'width': width,
                            'dtype': dtype
                        })

print(f"✓ Found {len(var_specs)} of {len(REQUIRED_VARS)} required variables in .dct")
print()

# Check which variables are missing
found_vars = {v['name'] for v in var_specs}
missing_vars = set(REQUIRED_VARS) - found_vars
if missing_vars:
    print(f"⚠️  Could not find {len(missing_vars)} variables:")
    for v in sorted(missing_vars):
        print(f"    - {v}")
    print()

dat_file = Path("data/childK5p.dat")
print(f"File size: {dat_file.stat().st_size / (1024**3):.2f} GB")
print("This will take 3-5 minutes...")
print()

# Read the file line by line, grouping every 27 lines
data_rows = []
current_record = []
line_count = 0

with open(dat_file, 'r', encoding='latin-1', errors='replace') as f:
    for line in f:
        line_count += 1
        current_record.append(line.rstrip('\n'))
        
        # Every 27 lines = 1 observation
        if len(current_record) == 27:
            # Extract variables from this record
            row = {}
            for var in var_specs:
                line_text = current_record[var['line'] - 1]  # 0-indexed
                start = var['col'] - 1  # 0-indexed
                end = start + var['width']
                
                value = line_text[start:end].strip()
                
                # Convert to appropriate type
                if var['dtype'] == 'int':
                    try:
                        row[var['name']] = int(value) if value else None
                    except ValueError:
                        row[var['name']] = None
                elif var['dtype'] == 'float':
                    try:
                        row[var['name']] = float(value) if value else None
                    except ValueError:
                        row[var['name']] = None
                else:
                    row[var['name']] = value if value else None
            
            data_rows.append(row)
            current_record = []
            
            # Progress indicator
            if len(data_rows) % 1000 == 0:
                print(f"  Processed {len(data_rows):,} children...", end='\r')


df_new = pd.DataFrame(data_rows)
print(f"New data: {len(df_new):,} rows × {len(df_new.columns)} columns")
print()

# Save the newly extracted variables
output_file = "data/ecls_missing_variables.csv"
df_new.to_csv(output_file, index=False)
print(f"✓ Saved: {output_file}")
print()

# Merge with existing ECLSData.csv

print("STEP 4: Merging with existing ECLSData.csv...")
print("-"*80)

df_existing = pd.read_csv("data/ECLSData.csv")
print(f"Existing data: {len(df_existing):,} rows × {len(df_existing.columns)} columns")

# Merge on CHILDID
df_existing['childid'] = df_existing['childid'].astype(str).str.strip()
df_new['CHILDID'] = df_new['CHILDID'].astype(str).str.strip()

df_complete = df_existing.merge(df_new, left_on='childid', right_on='CHILDID', how='left')
print(f"Merged data: {len(df_complete):,} rows × {len(df_complete.columns)} columns")
print()

# Save complete dataset
output_complete = "data_processed/ecls_complete.csv"
df_complete.to_csv(output_complete, index=False)
print(f"✓ Saved complete dataset: {output_complete}")
print()
