#!/usr/bin/env python3
import pandas as pd
import re
from pathlib import Path

REQUIRED_VARS = [
    # === FOOD SECURITY (with "2" suffix) ===
    "X2FSRAW2", "X2FSSCAL2", "X2FSSTAT2",  # Wave 2 (Spring K)
    "X2FSADRA2", "X2FSADSC2", "X2FSADST2",  # Adult measures
    "X2FSCHRA", "X2FSCHSC", "X2FSCHST",  # Child measures
    
    "X4FSRAW2", "X4FSSCAL2", "X4FSSTAT2",  # Wave 4 (Spring 1st)
    "X4FSADRA2", "X4FSADSC2", "X4FSADST2",
    "X4FSCHRA", "X4FSCHSC", "X4FSCHST",
    
    "X7FSADRA2", "X7FSADSC2", "X7FSADST2",  # Wave 7 (partial)
    "X8FSADRA2", "X8FSADSC2", "X8FSADST2",  # Wave 8 (partial)
    
    "X9FSRAW2", "X9FSSCAL2", "X9FSSTAT2",  # Wave 9 (Spring 5th)
    "X9FSADRA2", "X9FSADSC2", "X9FSADST2",
    "X9FSCHRA", "X9FSCHSC", "X9FSCHST",
    
    # Individual FS questions
    "P2WORRFD", "P2FDLAST", "P2NOMONY", "P2MOFDST",
    
    # === READING SCORES (already have math) ===
    "X1RSCALK5", "X2RSCALK5", "X3RSCALK5", "X4RSCALK5", "X5RSCALK5",
    "X6RSCALK5", "X7RSCALK5", "X8RSCALK5", "X9RSCALK5",
    
    # === TEACHER-RATED SOCIAL-EMOTIONAL ===
    # Approaches to learning
    "X1TCHAPP", "X2TCHAPP", "X4TCHAPP", "X6TCHAPP", "X7TCHAPP", "X8TCHAPP", "X9TCHAPP",
    # Self-control  
    "X1TCHCON", "X2TCHCON", "X4TCHCON", "X6TCHCON", "X7TCHCON", "X8TCHCON", "X9TCHCON",
    # Externalizing
    "X1TCHEXT", "X2TCHEXT", "X4TCHEXT", "X6TCHEXT", "X7TCHEXT", "X8TCHEXT", "X9TCHEXT",
    # Internalizing
    "X1TCHINT", "X2TCHINT", "X4TCHINT", "X6TCHINT", "X7TCHINT", "X8TCHINT", "X9TCHINT",
    
    # === DEMOGRAPHICS (with correct suffixes) ===
    "X_RACETH_R", "X_RACETHP_R",
    "X1KAGE_R", "X2KAGE_R",  # With _R suffix
    "X1FIRKDG", "X2FIRKDG",
    "X1HPARNT", "X2HPARNT", "X4HPARNT", "X6HPARNT", "X7HPARNT",
    
    # === SAMPLING WEIGHTS ===
    "W1C0", "W1P0", "W2P0", "W12P0",
    "W4CF4P_20", "W6CS6P_20", "W7C7P_20", "W9C9P_90",
    
    # === SCIENCE SCORES (bonus) ===
    "X2SSCALK5", "X4SSCALK5", "X6SSCALK5", "X7SSCALK5", "X8SSCALK5", "X9SSCALK5",
    
    # === ID VARIABLE ===
    "CHILDID"
]

print(f"Variables to extract: {len(REQUIRED_VARS)}")
print()


# Parse .dct file
dct_file = Path("data/ECLSK2011_K5PUF.dct")
var_specs = []
current_line_num = 1

with open(dct_file, 'r', encoding='latin-1', errors='replace') as f:
    for line in f:
        if '_line(' in line:
            match = re.search(r'_line\((\d+)\)', line)
            if match:
                current_line_num = int(match.group(1))
        
        if '_column(' in line:
            col_match = re.search(r'_column\((\d+)\)', line)
            if col_match:
                col_pos = int(col_match.group(1))
                parts = line.split()
                col_idx = next((i for i, p in enumerate(parts) if '_column' in p), None)
                
                if col_idx is not None and len(parts) > col_idx + 2:
                    var_type = parts[col_idx + 1]
                    var_name = parts[col_idx + 2]
                    
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
                    
                    if var_name.upper() in REQUIRED_VARS:
                        var_specs.append({
                            'name': var_name.upper(),
                            'line': current_line_num,
                            'col': col_pos,
                            'width': width,
                            'dtype': dtype
                        })

print(f"✓ Found {len(var_specs)} of {len(REQUIRED_VARS)} variables")

found_vars = {v['name'] for v in var_specs}
missing_vars = set(REQUIRED_VARS) - found_vars
if missing_vars:
    print(f"\n⚠️  Missing {len(missing_vars)} variables:")
    for v in sorted(list(missing_vars)[:20]):
        print(f"    {v}")
    if len(missing_vars) > 20:
        print(f"    ... and {len(missing_vars) - 20} more")
print()

dat_file = Path("data/childK5p.dat")
print(f"Processing 2.29 GB file (3-5 minutes)...")
print()

data_rows = []
current_record = []

with open(dat_file, 'r', encoding='latin-1', errors='replace') as f:
    for line in f:
        current_record.append(line.rstrip('\n'))
        
        if len(current_record) == 27:
            row = {}
            for var in var_specs:
                line_text = current_record[var['line'] - 1]
                start = var['col'] - 1
                end = start + var['width']
                value = line_text[start:end].strip()
                
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
            
            if len(data_rows) % 1000 == 0:
                print(f"  {len(data_rows):,} children processed...", end='\r')

df_new = pd.DataFrame(data_rows)
df_new.to_csv("data/ecls_all_missing_vars.csv", index=False)
print(f"✓ Saved: data/ecls_all_missing_vars.csv ({len(df_new.columns)} vars)")

# Merge with existing
df_existing = pd.read_csv("data/ECLSData.csv")
df_existing['childid'] = df_existing['childid'].astype(str).str.strip()
df_new['CHILDID'] = df_new['CHILDID'].astype(str).str.strip()

df_complete = df_existing.merge(df_new, left_on='childid', right_on='CHILDID', how='left')
output = "data_processed/ecls_complete_final.csv"
df_complete.to_csv(output, index=False)

print(f"✓ Complete dataset: {len(df_complete):,} rows × {len(df_complete.columns)} columns")
print(f"✓ Saved: {output}")
print()
