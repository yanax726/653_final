#!/usr/bin/env python3
import re
from pathlib import Path

# Read the .dct file
dct_file = Path("data/ECLSK2011_K5PUF.dct")

all_variables = []

with open(dct_file, 'r', encoding='latin-1', errors='replace') as f:
    for line in f:
        if '_column(' in line:
            parts = line.split()
            col_idx = next((i for i, p in enumerate(parts) if '_column' in p), None)
            
            if col_idx is not None and len(parts) > col_idx + 2:
                var_name = parts[col_idx + 2]
                # Get variable description (in quotes)
                desc_match = re.search(r'"([^"]*)"', line)
                desc = desc_match.group(1) if desc_match else ""
                
                all_variables.append({
                    'name': var_name,
                    'line': line.strip(),
                    'desc': desc
                })

print(f"Total variables found: {len(all_variables)}")
print()

# =============================================================================
# SEARCH 1: Food Security Variables
# =============================================================================
print("SEARCH 1: FOOD SECURITY VARIABLES")
print("-"*80)

# Search patterns for food security
fs_patterns = [
    'FOOD', 'FS', 'FSEC', 'INSEC', 'HUNGER', 'MEAL',
    'USDA', 'SNAP', 'WIC', 'LUNCH'
]

print("Searching for variables containing: 'FOOD', 'FS', 'INSEC', etc.")
print()

fs_vars = []
for var in all_variables:
    var_upper = var['name'].upper()
    desc_upper = var['desc'].upper()
    
    if any(pattern in var_upper or pattern in desc_upper for pattern in fs_patterns):
        fs_vars.append(var)

if fs_vars:
    print(f"✓ Found {len(fs_vars)} potential food security variables:")
    print()
    for v in fs_vars[:50]:  # Show first 50
        print(f"  Variable: {v['name']}")
        print(f"    Description: {v['desc']}")
        print()
else:
    print("No food security variables found with these patterns")
    print()

# Weights

weight_vars = [v for v in all_variables if v['name'].upper().startswith('W') 
               and 'WEIGHT' in v['desc'].upper() or 'WGT' in v['desc'].upper()]

if weight_vars:
    print(f"✓ Found {len(weight_vars)} weight variables:")
    print()
    for v in weight_vars[:20]:  # Show first 20
        print(f"  {v['name']}: {v['desc']}")
else:
    print("Searching for weights with 'C0' pattern...")
    weight_vars = [v for v in all_variables if 'C0' in v['name'].upper()]
    print(f"Found {len(weight_vars)} variables with 'C0':")
    for v in weight_vars[:20]:
        print(f"  {v['name']}: {v['desc']}")

print()

# Age and Demographics


demo_patterns = [
    ('AGE', 'X1KAGE'),
    ('RACE', 'X_RACETH_R'),
    ('FIRKDG', 'X1FIRKDG'),
    ('HPARNT', 'X1HPARNT')
]

for pattern, expected in demo_patterns:
    matches = [v for v in all_variables if pattern in v['name'].upper()]
    print(f"\nSearching for '{pattern}' (expected: {expected}):")
    if matches:
        for v in matches[:5]:
            print(f"  {v['name']}: {v['desc']}")
    else:
        print(f"  Not found")

# 4. List all X1, X2, X4, X6, X7, X8, X9 variables

for wave in ['X1', 'X2', 'X4', 'X6', 'X7', 'X8', 'X9']:
    wave_vars = [v for v in all_variables if v['name'].upper().startswith(wave)]
    print(f"\n{wave} variables: {len(wave_vars)}")
    
    # Look specifically for ones that might be food security
    potential_fs = [v for v in wave_vars if len(v['name']) <= 10]
    if potential_fs and wave in ['X1', 'X2', 'X4', 'X6', 'X7', 'X8', 'X9']:
        print(f"  First 30 {wave} variables:")
        for v in potential_fs[:30]:
            print(f"    {v['name']}: {v['desc']}")
