# Reshape ECLS-K data from wide to long format for longitudinal analysis
# Keeps waves 2, 4, and 9 (Spring K, Spring 1st, Spring 5th)
# Food security data is only available in these waves

import pandas as pd
import numpy as np

print("Reading data...")
df = pd.read_csv("data/ecls_complete_final.csv")
print(f"Loaded {len(df):,} children with {df.shape[1]} variables\n")

# Variables that don't change over time
baseline_vars = [
    'childid', 'CHILDID', 'PARENTID', 'PSUID',
    'x_chsex_r', 'X_RACETHP_R', 'X1FIRKDG', 'X1KAGE_R',
    'x12sesl', 'x_distpov',
    'x12par1ed_i', 'x12par2ed_i', 'X1HPARNT'
]

# Variables measured at each wave (with wave-specific column names)
wave_vars = {
    # Outcomes
    'math': {2: 'x2mscalk5', 4: 'x4mscalk5', 9: 'x9mscalk5'},
    'science': {2: 'X2SSCALK5', 4: 'X4SSCALK5', 9: 'X9SSCALK5'},

    # Food security
    'fs_raw': {2: 'X2FSRAW2', 4: 'X4FSRAW2', 9: 'X9FSRAW2'},
    'fs_scale': {2: 'X2FSSCAL2', 4: 'X4FSSCAL2', 9: 'X9FSSCAL2'},
    'fs_status': {2: 'X2FSSTAT2', 4: 'X4FSSTAT2', 9: 'X9FSSTAT2'},
    'fs_adult_raw': {2: 'X2FSADRA2', 4: 'X4FSADRA2', 9: 'X9FSADRA2'},
    'fs_adult_scale': {2: 'X2FSADSC2', 4: 'X4FSADSC2', 9: 'X9FSADSC2'},
    'fs_adult_status': {2: 'X2FSADST2', 4: 'X4FSADST2', 9: 'X9FSADST2'},
    'fs_child_raw': {2: 'X2FSCHRA', 4: 'X4FSCHRA', 9: 'X9FSCHRA'},
    'fs_child_scale': {2: 'X2FSCHSC', 4: 'X4FSCHSC', 9: 'X9FSCHSC'},
    'fs_child_status': {2: 'X2FSCHST', 4: 'X4FSCHST', 9: 'X9FSCHST'},

    # Teacher ratings
    'tch_approaches': {2: 'X2TCHAPP', 4: 'X4TCHAPP'},
    'tch_control': {2: 'X2TCHCON', 4: 'X4TCHCON'},
    'tch_external': {2: 'X2TCHEXT', 4: 'X4TCHEXT'},
    'tch_internal': {2: 'X2TCHINT', 4: 'X4TCHINT'},
    'tch_close': {2: 'X2CLSNSS', 4: 'X4CLSNSS'},
    'tch_conflict': {2: 'X2CNFLCT', 4: 'X4CNFLCT'},

    # Executive function
    'attention': {2: 'X2ATTNFS', 4: 'X4ATTNFS', 9: 'X9ATTMCQ'},
    'inhibit': {2: 'X2INBCNT', 4: 'X4INBCNT', 9: 'X9INTMCQ'},

    # School
    'school_id': {2: 's2_id', 4: 's4_id', 9: 's9_id'},
    'school_type': {2: 'x2ksctyp', 4: 'x4sctyp', 9: 'x9sctyp'},
    'school_size': {2: 'x2kenrls', 4: 'x4enrls', 9: 'x9enrls'},
    'urbanicity': {2: 'x2locale', 4: 'x4locale', 9: 'x9locale'},

    # Family
    'income': {2: 'x2inccat_i', 4: 'x4inccat_i', 9: 'x9inccat_i'},
    'ses': {2: 'x2sesl_i', 4: 'x4sesl_i', 9: 'x9sesl_i'},
    'hh_size': {2: 'x2htotal', 4: 'x4htotal', 9: 'x9htotal'},
    'n_parents': {2: 'X2HPARNT', 4: 'X4HPARNT', 9: 'X9HPARNT'},
    'par1_ed': {2: 'x4par1ed_i', 4: 'x4par1ed_i', 9: 'x9par1ed_i'},
    'par2_ed': {2: 'x4par2ed_i', 4: 'x4par2ed_i', 9: 'x9par2ed_i'},
    'par1_emp': {2: 'x1par1emp', 4: 'x4par1emp_i', 9: 'x9par1emp_i'},
    'par2_emp': {2: 'x1par2emp', 4: 'x4par2emp_i', 9: 'x9par2emp_i'},

    # Child physical
    'height': {2: 'x2height', 4: 'x4height', 9: 'x9height'},
    'weight': {2: 'x2weight', 4: 'x4weight', 9: 'x9weight'},
    'bmi': {2: 'x2bmi', 4: 'x4bmi', 9: 'x9bmi'},
    'disability': {2: 'x2disabl', 4: 'x4disabl', 9: 'x9disabl'},

    # Weights
    'wt_parent': {2: 'W2P0'},
    'wt_child': {4: 'W4CF4P_20', 9: 'W9C9P_20'},
}

# Reshape to long format
print("Reshaping to long format...")
waves = [2, 4, 9]
dfs = []

for w in waves:
    temp = df[baseline_vars].copy()
    temp['wave'] = w

    for var, mapping in wave_vars.items():
        if w in mapping and mapping[w] in df.columns:
            temp[var] = df[mapping[w]]
        else:
            temp[var] = np.nan

    dfs.append(temp)

long_df = pd.concat(dfs, ignore_index=True)

print(f"Created long format: {len(long_df):,} rows x {long_df.shape[1]} columns")
print(f"  {len(df):,} children x {len(waves)} waves = {len(df) * len(waves):,} observations\n")

# Save
long_df.to_csv("data/ecls_long.csv", index=False)
print("Saved to data/ecls_long.csv")
