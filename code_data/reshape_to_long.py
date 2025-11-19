#!/usr/bin/env python3
"""
Reshape ECLS-K data from wide format to long format
Only keep waves 2, 4, 9 (where food security data is available)

NOTE: Reading scores (xNrscalk5) are NOT available in the source data.
Only math and science scores are included.
The proposal mentions reading + math, but we can only use math + science.
"""

import pandas as pd
import numpy as np

print("="*80)
print("RESHAPING ECLS-K DATA: WIDE TO LONG FORMAT")
print("Keeping only waves 2, 4, 9")
print("="*80)
print()

# Read the wide format data
print("Step 1: Reading wide format data...")
df_wide = pd.read_csv("data/ecls_complete_final.csv")
print(f"  Wide format: {df_wide.shape[0]:,} rows × {df_wide.shape[1]} columns")
print()

# Identify time-invariant variables (child-level characteristics)
# These don't change across waves
time_invariant = [
    'childid',
    'CHILDID', 'PARENTID', 'PSUID',
    'x_chsex_r',           # Sex
    'X_RACETHP_R',         # Race/ethnicity
    'X1FIRKDG',            # First-time kindergartner
    'X1KAGE_R',            # Age at K entry
    'x12sesl',             # Baseline SES
    'x_distpov',           # District poverty (baseline)
    'x12par1ed_i',         # Parent 1 education (baseline)
    'x12par2ed_i',         # Parent 2 education (baseline)
    'X1HPARNT',            # Number of parents in HH (baseline)
]

# Define time-varying variables for waves 2, 4, 9
# Format: {new_name: {wave: old_column_name}}
time_varying_vars = {
    # Academic outcomes
    'math_score': {2: 'x2mscalk5', 4: 'x4mscalk5', 9: 'x9mscalk5'},
    'science_score': {2: 'X2SSCALK5', 4: 'X4SSCALK5', 9: 'X9SSCALK5'},

    # Food security - raw scores
    'fs_raw': {2: 'X2FSRAW2', 4: 'X4FSRAW2', 9: 'X9FSRAW2'},
    'fs_scale': {2: 'X2FSSCAL2', 4: 'X4FSSCAL2', 9: 'X9FSSCAL2'},
    'fs_status': {2: 'X2FSSTAT2', 4: 'X4FSSTAT2', 9: 'X9FSSTAT2'},

    # Food security - adult
    'fs_adult_raw': {2: 'X2FSADRA2', 4: 'X4FSADRA2', 9: 'X9FSADRA2'},
    'fs_adult_scale': {2: 'X2FSADSC2', 4: 'X4FSADSC2', 9: 'X9FSADSC2'},
    'fs_adult_status': {2: 'X2FSADST2', 4: 'X4FSADST2', 9: 'X9FSADST2'},

    # Food security - child
    'fs_child_raw': {2: 'X2FSCHRA', 4: 'X4FSCHRA', 9: 'X9FSCHRA'},
    'fs_child_scale': {2: 'X2FSCHSC', 4: 'X4FSCHSC', 9: 'X9FSCHSC'},
    'fs_child_status': {2: 'X2FSCHST', 4: 'X4FSCHST', 9: 'X9FSCHST'},

    # Teacher-rated socioemotional (note: not all available in wave 9)
    'tch_approaches': {2: 'X2TCHAPP', 4: 'X4TCHAPP'},
    'tch_selfcontrol': {2: 'X2TCHCON', 4: 'X4TCHCON'},
    'tch_externalizing': {2: 'X2TCHEXT', 4: 'X4TCHEXT'},
    'tch_internalizing': {2: 'X2TCHINT', 4: 'X4TCHINT'},

    # Teacher-child relationship
    'tch_closeness': {2: 'X2CLSNSS', 4: 'X4CLSNSS'},
    'tch_conflict': {2: 'X2CNFLCT', 4: 'X4CNFLCT'},

    # Executive function
    'attention': {2: 'X2ATTNFS', 4: 'X4ATTNFS', 9: 'X9ATTMCQ'},
    'inhibitory_control': {2: 'X2INBCNT', 4: 'X4INBCNT', 9: 'X9INTMCQ'},

    # School characteristics
    'school_id': {2: 's2_id', 4: 's4_id', 9: 's9_id'},
    'school_type': {2: 'x2ksctyp', 4: 'x4sctyp', 9: 'x9sctyp'},
    'school_enrollment': {2: 'x2kenrls', 4: 'x4enrls', 9: 'x9enrls'},
    'locale': {2: 'x2locale', 4: 'x4locale', 9: 'x9locale'},

    # Family characteristics (time-varying)
    'income_category': {2: 'x2inccat_i', 4: 'x4inccat_i', 9: 'x9inccat_i'},
    'ses': {2: 'x4sesl_i', 4: 'x4sesl_i', 9: 'x9sesl_i'},  # Time-varying SES (note: x2sesl_i may not exist, using x4sesl_i for wave 2)
    'household_size': {2: 'x2htotal', 4: 'x4htotal', 9: 'x9htotal'},
    'parents_home': {2: 'X2HPARNT', 4: 'X4HPARNT', 9: 'X9HPARNT'},
    'parent1_ed': {2: 'x4par1ed_i', 4: 'x4par1ed_i', 9: 'x9par1ed_i'},  # Time-varying parent education
    'parent2_ed': {2: 'x4par2ed_i', 4: 'x4par2ed_i', 9: 'x9par2ed_i'},

    # Child characteristics (time-varying)
    'height': {2: 'x2height', 4: 'x4height', 9: 'x9height'},
    'weight': {2: 'x2weight', 4: 'x4weight', 9: 'x9weight'},
    'bmi': {2: 'x2bmi', 4: 'x4bmi', 9: 'x9bmi'},
    'disability': {2: 'x2disabl', 4: 'x4disabl', 9: 'x9disabl'},
    'age': {2: 'X2KAGE_R'},  # Only wave 2 has this

    # Sampling weights
    'weight_parent': {2: 'W2P0'},
    'weight_longitudinal': {4: 'W4CF4P_20', 9: 'W9C9P_20'},
}

# Step 2: Create long format data
print("Step 2: Reshaping to long format...")
print()

waves = [2, 4, 9]
long_data = []

for wave in waves:
    print(f"  Processing Wave {wave}...")

    # Start with time-invariant variables
    wave_df = df_wide[time_invariant].copy()
    wave_df['wave'] = wave

    # Add time-varying variables for this wave
    for var_name, wave_dict in time_varying_vars.items():
        if wave in wave_dict:
            col_name = wave_dict[wave]
            if col_name in df_wide.columns:
                wave_df[var_name] = df_wide[col_name]
            else:
                wave_df[var_name] = np.nan
        else:
            # Variable not available for this wave
            wave_df[var_name] = np.nan

    long_data.append(wave_df)

# Combine all waves
df_long = pd.concat(long_data, ignore_index=True)

print()
print(f"  Long format: {df_long.shape[0]:,} rows × {df_long.shape[1]} columns")
print(f"  ({len(df_wide):,} children × {len(waves)} waves = {len(df_wide) * len(waves):,} expected rows)")
print()

# Step 3: Data quality checks
print("Step 3: Data quality checks...")
print()

# Check wave distribution
print("  Wave distribution:")
print(df_long['wave'].value_counts().sort_index())
print()

# Check food security data availability
print("  Food security data availability by wave:")
for wave in waves:
    wave_data = df_long[df_long['wave'] == wave]
    fs_available = wave_data['fs_status'].notna().sum()
    pct = (fs_available / len(wave_data)) * 100
    print(f"    Wave {wave}: {fs_available:,}/{len(wave_data):,} ({pct:.1f}%)")
print()

# Check math score availability
print("  Math score data availability by wave:")
for wave in waves:
    wave_data = df_long[df_long['wave'] == wave]
    math_available = wave_data['math_score'].notna().sum()
    pct = (math_available / len(wave_data)) * 100
    print(f"    Wave {wave}: {math_available:,}/{len(wave_data):,} ({pct:.1f}%)")
print()

# Step 4: Save long format data
print("Step 4: Saving long format data...")

output_file = "data/ecls_long_format.csv"
df_long.to_csv(output_file, index=False)
print(f"  ✓ Saved: {output_file}")
print()

# Also save a data dictionary
dict_file = "data/ecls_long_format_dictionary.txt"
with open(dict_file, 'w') as f:
    f.write("ECLS-K LONG FORMAT DATA DICTIONARY\n")
    f.write("="*80 + "\n\n")
    f.write(f"Total observations: {len(df_long):,}\n")
    f.write(f"Unique children: {df_long['childid'].nunique():,}\n")
    f.write(f"Waves: {', '.join(map(str, waves))}\n\n")

    f.write("TIME-INVARIANT VARIABLES:\n")
    f.write("-"*80 + "\n")
    for var in time_invariant:
        if var in df_long.columns:
            f.write(f"  {var}\n")
    f.write("\n")

    f.write("TIME-VARYING VARIABLES:\n")
    f.write("-"*80 + "\n")
    for var_name in sorted(time_varying_vars.keys()):
        non_missing = df_long[var_name].notna().sum()
        pct = (non_missing / len(df_long)) * 100
        f.write(f"  {var_name:<25} ({non_missing:,} non-missing, {pct:.1f}%)\n")
    f.write("\n")

    f.write("WAVE-SPECIFIC AVAILABILITY:\n")
    f.write("-"*80 + "\n")
    for var_name, wave_dict in sorted(time_varying_vars.items()):
        f.write(f"\n  {var_name}:\n")
        for wave in waves:
            if wave in wave_dict:
                wave_data = df_long[df_long['wave'] == wave]
                non_missing = wave_data[var_name].notna().sum()
                pct = (non_missing / len(wave_data)) * 100 if len(wave_data) > 0 else 0
                f.write(f"    Wave {wave}: {wave_dict[wave]:<20} ({non_missing:,}, {pct:.1f}%)\n")
            else:
                f.write(f"    Wave {wave}: Not available\n")

print(f"  ✓ Saved: {dict_file}")
print()

# Step 5: Summary statistics
print("="*80)
print("SUMMARY")
print("="*80)
print()
print(f"Output file: {output_file}")
print(f"Dimensions: {df_long.shape[0]:,} rows × {df_long.shape[1]} columns")
print()
print("Key variables included:")
print("  - Food security: raw scores, scale scores, status (adult, child, combined)")
print("  - Academic outcomes: math scores, science scores")
print("  - Socioemotional: teacher ratings, relationship quality")
print("  - Covariates: demographics, SES, school characteristics")
print()
print("Next steps:")
print("  1. Load data in R/Python: pd.read_csv('data/ecls_long_format.csv')")
print("  2. Create trajectory groups using latent class growth analysis")
print("  3. Run multilevel models with wave nested in children")
print()
print("="*80)