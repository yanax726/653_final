#!/usr/bin/env python3
"""
Create TWO versions of ECLS-K long format data:
1. FLEXIBLE version: Variables available in wave 2 OR 4 OR 9 (may have missing wave 9)
2. COMPLETE version: Variables available in ALL waves 2 AND 4 AND 9

Also searches for alternative variables with similar meanings when data is incomplete.
"""

import pandas as pd
import numpy as np

print("="*80)
print("CREATING TWO VERSIONS OF ECLS-K LONG FORMAT DATA")
print("="*80)
print()

# Read the wide format data
print("Step 1: Reading wide format data...")
df_wide = pd.read_csv("data/ecls_complete_final.csv")
print(f"  Wide format: {df_wide.shape[0]:,} rows × {df_wide.shape[1]} columns")
print()

# Get all column names for searching
all_columns = df_wide.columns.tolist()

# Time-invariant variables (same for both versions)
time_invariant = [
    'childid',
    'CHILDID', 'PARENTID', 'PSUID',
    'x_chsex_r',           # Sex
    'X_RACETHP_R',         # Race/ethnicity
    'X1FIRKDG',            # First-time kindergartner
    'X1KAGE_R',            # Age at K entry
    'x12sesl',             # Baseline SES composite
    'x_distpov',           # District poverty
    'x12par1ed_i',         # Parent 1 education (baseline)
    'x12par2ed_i',         # Parent 2 education (baseline)
    'X1HPARNT',            # Number of parents (baseline)
]

# =============================================================================
# DEFINE ALL POSSIBLE TIME-VARYING VARIABLES
# =============================================================================

# Check availability for each variable across waves
def check_variable_exists(var_name):
    """Check if a variable exists in the data"""
    return var_name in all_columns

print("Step 2: Checking variable availability across waves...")
print()

# Define potential variables and check which waves they exist in
all_potential_vars = {
    # ===== ACADEMIC OUTCOMES =====
    'math_score': {2: 'x2mscalk5', 4: 'x4mscalk5', 9: 'x9mscalk5'},
    'science_score': {2: 'X2SSCALK5', 4: 'X4SSCALK5', 9: 'X9SSCALK5'},

    # ===== FOOD SECURITY - COMBINED =====
    'fs_raw': {2: 'X2FSRAW2', 4: 'X4FSRAW2', 9: 'X9FSRAW2'},
    'fs_scale': {2: 'X2FSSCAL2', 4: 'X4FSSCAL2', 9: 'X9FSSCAL2'},
    'fs_status': {2: 'X2FSSTAT2', 4: 'X4FSSTAT2', 9: 'X9FSSTAT2'},

    # ===== FOOD SECURITY - ADULT =====
    'fs_adult_raw': {2: 'X2FSADRA2', 4: 'X4FSADRA2', 9: 'X9FSADRA2'},
    'fs_adult_scale': {2: 'X2FSADSC2', 4: 'X4FSADSC2', 9: 'X9FSADSC2'},
    'fs_adult_status': {2: 'X2FSADST2', 4: 'X4FSADST2', 9: 'X9FSADST2'},

    # ===== FOOD SECURITY - CHILD =====
    'fs_child_raw': {2: 'X2FSCHRA', 4: 'X4FSCHRA', 9: 'X9FSCHRA'},
    'fs_child_scale': {2: 'X2FSCHSC', 4: 'X4FSCHSC', 9: 'X9FSCHSC'},
    'fs_child_status': {2: 'X2FSCHST', 4: 'X4FSCHST', 9: 'X9FSCHST'},

    # ===== TEACHER SOCIOEMOTIONAL =====
    'tch_approaches': {2: 'X2TCHAPP', 4: 'X4TCHAPP'},  # NOT in wave 9
    'tch_selfcontrol': {2: 'X2TCHCON', 4: 'X4TCHCON'},
    'tch_externalizing': {2: 'X2TCHEXT', 4: 'X4TCHEXT'},
    'tch_internalizing': {2: 'X2TCHINT', 4: 'X4TCHINT'},

    # ===== TEACHER-CHILD RELATIONSHIP =====
    'tch_closeness': {2: 'X2CLSNSS', 4: 'X4CLSNSS'},  # NOT in wave 9
    'tch_conflict': {2: 'X2CNFLCT', 4: 'X4CNFLCT'},

    # ===== EXECUTIVE FUNCTION =====
    'attention': {2: 'X2ATTNFS', 4: 'X4ATTNFS', 9: 'X9ATTMCQ'},
    'inhibitory_control': {2: 'X2INBCNT', 4: 'X4INBCNT', 9: 'X9INTMCQ'},

    # ===== SCHOOL CHARACTERISTICS =====
    'school_id': {2: 's2_id', 4: 's4_id', 9: 's9_id'},
    'school_type': {2: 'x2ksctyp', 4: 'x4sctyp', 9: 'x9sctyp'},
    'school_enrollment': {2: 'x2kenrls', 4: 'x4enrls', 9: 'x9enrls'},
    'locale': {2: 'x2locale', 4: 'x4locale', 9: 'x9locale'},

    # ===== FAMILY SES - TIME VARYING =====
    # NOTE: Searching for best SES variable
    'ses': {2: 'x2sesl_i', 4: 'x4sesl_i', 9: 'x9sesl_i'},  # Time-varying SES
    'income_category': {2: 'x2inccat_i', 4: 'x4inccat_i', 9: 'x9inccat_i'},

    # ===== FAMILY STRUCTURE =====
    'household_size': {2: 'x2htotal', 4: 'x4htotal', 9: 'x9htotal'},
    'parents_home': {2: 'X2HPARNT', 4: 'X4HPARNT', 9: 'X9HPARNT'},  # Check wave 9
    'parent1_ed': {2: 'x4par1ed_i', 4: 'x4par1ed_i', 9: 'x9par1ed_i'},
    'parent2_ed': {2: 'x4par2ed_i', 4: 'x4par2ed_i', 9: 'x9par2ed_i'},

    # ===== PARENT EMPLOYMENT =====
    'parent1_emp': {2: 'x1par1emp', 4: 'x4par1emp_i', 9: 'x9par1emp_i'},  # Check wave 2
    'parent2_emp': {2: 'x1par2emp', 4: 'x4par2emp_i', 9: 'x9par2emp_i'},

    # ===== CHILD PHYSICAL =====
    'height': {2: 'x2height', 4: 'x4height', 9: 'x9height'},
    'weight': {2: 'x2weight', 4: 'x4weight', 9: 'x9weight'},
    'bmi': {2: 'x2bmi', 4: 'x4bmi', 9: 'x9bmi'},
    'disability': {2: 'x2disabl', 4: 'x4disabl', 9: 'x9disabl'},
    'age': {2: 'X2KAGE_R', 4: 'X4KAGE_R', 9: 'X9KAGE_R'},  # Check all waves

    # ===== SAMPLING WEIGHTS =====
    'weight_parent': {2: 'W2P0'},
    'weight_longitudinal': {4: 'W4CF4P_20', 9: 'W9C9P_20'},
}

# Check which variables actually exist and categorize them
flexible_vars = {}  # Variables in 2 OR 4 OR 9
complete_vars = {}  # Variables in 2 AND 4 AND 9
incomplete_vars = {}  # Variables NOT in all waves

print("VARIABLE AVAILABILITY CHECK:")
print("-" * 80)

for var_name, wave_dict in all_potential_vars.items():
    # Check which waves actually have this variable
    available_waves = {}
    for wave, col_name in wave_dict.items():
        if check_variable_exists(col_name):
            available_waves[wave] = col_name

    # Determine if complete (has all 2, 4, 9)
    has_wave_2 = 2 in available_waves
    has_wave_4 = 4 in available_waves
    has_wave_9 = 9 in available_waves

    is_complete = has_wave_2 and has_wave_4 and has_wave_9
    is_flexible = has_wave_2 or has_wave_4 or has_wave_9

    if is_flexible:
        flexible_vars[var_name] = available_waves

    if is_complete:
        complete_vars[var_name] = available_waves
        status = "✓ COMPLETE (2,4,9)"
    else:
        incomplete_vars[var_name] = available_waves
        waves_str = ",".join(map(str, sorted(available_waves.keys())))
        status = f"⚠ INCOMPLETE (only {waves_str})"

    print(f"  {var_name:<25} {status}")

print()
print(f"Summary:")
print(f"  - FLEXIBLE version variables: {len(flexible_vars)}")
print(f"  - COMPLETE version variables: {len(complete_vars)}")
print(f"  - INCOMPLETE variables: {len(incomplete_vars)}")
print()

# =============================================================================
# SEARCH FOR ALTERNATIVE VARIABLES FOR INCOMPLETE ONES
# =============================================================================

print("Step 3: Searching for alternative variables for incomplete ones...")
print("-" * 80)

# Define search patterns for alternatives
alternatives_found = {}

# Check for wave 2 SES variable
if check_variable_exists('x2sesl_i'):
    print("  ✓ Found x2sesl_i for wave 2 SES (updating ses variable)")
    flexible_vars['ses'] = {2: 'x2sesl_i', 4: 'x4sesl_i', 9: 'x9sesl_i'}
    complete_vars['ses'] = {2: 'x2sesl_i', 4: 'x4sesl_i', 9: 'x9sesl_i'}
    alternatives_found['ses'] = "Updated to use x2sesl_i for wave 2"

# Check for X9HPARNT (parents home wave 9)
if check_variable_exists('X9HPARNT'):
    print("  ✓ Found X9HPARNT for wave 9 parents at home")
    flexible_vars['parents_home'][9] = 'X9HPARNT'
    complete_vars['parents_home'] = {2: 'X2HPARNT', 4: 'X4HPARNT', 9: 'X9HPARNT'}
    alternatives_found['parents_home'] = "Found X9HPARNT for wave 9"

# Check for wave 2 parent employment
if check_variable_exists('x2par1emp_i'):
    print("  ✓ Found x2par1emp_i for wave 2 parent 1 employment")
    flexible_vars['parent1_emp'] = {2: 'x2par1emp_i', 4: 'x4par1emp_i', 9: 'x9par1emp_i'}
    if check_variable_exists('x9par1emp_i'):
        complete_vars['parent1_emp'] = {2: 'x2par1emp_i', 4: 'x4par1emp_i', 9: 'x9par1emp_i'}

if check_variable_exists('x2par2emp_i'):
    print("  ✓ Found x2par2emp_i for wave 2 parent 2 employment")
    flexible_vars['parent2_emp'] = {2: 'x2par2emp_i', 4: 'x4par2emp_i', 9: 'x9par2emp_i'}
    if check_variable_exists('x9par2emp_i'):
        complete_vars['parent2_emp'] = {2: 'x2par2emp_i', 4: 'x4par2emp_i', 9: 'x9par2emp_i'}

# Check for age in all waves
age_complete = True
age_dict = {}
for wave in [2, 4, 9]:
    age_var = f'X{wave}KAGE_R'
    if check_variable_exists(age_var):
        age_dict[wave] = age_var
    else:
        age_complete = False

if age_complete:
    print(f"  ✓ Found age variables for all waves: {age_dict}")
    flexible_vars['age'] = age_dict
    complete_vars['age'] = age_dict
    alternatives_found['age'] = "Found age for all waves"

print()
print(f"Alternatives found: {len(alternatives_found)}")
for var, desc in alternatives_found.items():
    print(f"  - {var}: {desc}")
print()

# =============================================================================
# UPDATE INCOMPLETE VARIABLES LIST
# =============================================================================

# Recalculate incomplete after finding alternatives
still_incomplete = []
for var_name, wave_dict in flexible_vars.items():
    if var_name not in complete_vars:
        waves_str = ",".join(map(str, sorted(wave_dict.keys())))
        still_incomplete.append(f"{var_name} (waves {waves_str})")

print("Variables still incomplete after searching for alternatives:")
print("-" * 80)
if still_incomplete:
    for item in still_incomplete:
        print(f"  ⚠ {item}")
else:
    print("  ✓ All flexible variables are now complete!")
print()

# =============================================================================
# CREATE BOTH VERSIONS
# =============================================================================

def create_long_format(var_dict, version_name):
    """Create long format data with given variables"""
    waves = [2, 4, 9]
    long_data = []

    for wave in waves:
        # Start with time-invariant variables
        wave_df = df_wide[time_invariant].copy()
        wave_df['wave'] = wave

        # Add time-varying variables
        for var_name, wave_mapping in var_dict.items():
            if wave in wave_mapping:
                col_name = wave_mapping[wave]
                if col_name in df_wide.columns:
                    wave_df[var_name] = df_wide[col_name]
                else:
                    wave_df[var_name] = np.nan
            else:
                wave_df[var_name] = np.nan

        long_data.append(wave_df)

    df_long = pd.concat(long_data, ignore_index=True)

    print(f"  {version_name}:")
    print(f"    Dimensions: {df_long.shape[0]:,} rows × {df_long.shape[1]} columns")
    print(f"    Variables: {len(var_dict)} time-varying + {len(time_invariant)} time-invariant")

    return df_long

print("Step 4: Creating both versions...")
print("-" * 80)

# VERSION 1: FLEXIBLE (2 OR 4 OR 9)
df_flexible = create_long_format(flexible_vars, "VERSION 1 - FLEXIBLE")

# VERSION 2: COMPLETE (2 AND 4 AND 9)
df_complete = create_long_format(complete_vars, "VERSION 2 - COMPLETE")

print()

# =============================================================================
# SAVE BOTH VERSIONS
# =============================================================================

print("Step 5: Saving both versions...")
print("-" * 80)

# Save flexible version
flexible_file = "data/ecls_long_FLEXIBLE.csv"
df_flexible.to_csv(flexible_file, index=False)
print(f"  ✓ Saved: {flexible_file}")

# Save complete version
complete_file = "data/ecls_long_COMPLETE.csv"
df_complete.to_csv(complete_file, index=False)
print(f"  ✓ Saved: {complete_file}")

print()

# =============================================================================
# CREATE COMPARISON REPORT
# =============================================================================

print("Step 6: Creating comparison report...")
print("-" * 80)

report_file = "data/VERSION_COMPARISON_REPORT.txt"
with open(report_file, 'w') as f:
    f.write("="*80 + "\n")
    f.write("ECLS-K LONG FORMAT DATA: VERSION COMPARISON REPORT\n")
    f.write("="*80 + "\n\n")

    f.write("TWO VERSIONS CREATED:\n\n")

    f.write("1. FLEXIBLE VERSION (data/ecls_long_FLEXIBLE.csv)\n")
    f.write("   - Includes variables if they exist in waves 2 OR 4 OR 9\n")
    f.write(f"   - {df_flexible.shape[0]:,} rows × {df_flexible.shape[1]} columns\n")
    f.write(f"   - {len(flexible_vars)} time-varying variables\n")
    f.write("   - Some variables may have missing data in wave 9\n")
    f.write("   - USE THIS for maximum variable coverage\n\n")

    f.write("2. COMPLETE VERSION (data/ecls_long_COMPLETE.csv)\n")
    f.write("   - ONLY includes variables that exist in ALL waves 2 AND 4 AND 9\n")
    f.write(f"   - {df_complete.shape[0]:,} rows × {df_complete.shape[1]} columns\n")
    f.write(f"   - {len(complete_vars)} time-varying variables\n")
    f.write("   - All variables have data structure for all 3 waves\n")
    f.write("   - USE THIS for balanced longitudinal analysis\n\n")

    f.write("="*80 + "\n")
    f.write("VARIABLES IN FLEXIBLE VERSION (2 OR 4 OR 9)\n")
    f.write("="*80 + "\n\n")

    for var_name in sorted(flexible_vars.keys()):
        waves_avail = sorted(flexible_vars[var_name].keys())
        wave_str = ", ".join(map(str, waves_avail))
        f.write(f"  {var_name:<30} waves: {wave_str}\n")

    f.write("\n")
    f.write("="*80 + "\n")
    f.write("VARIABLES IN COMPLETE VERSION (2 AND 4 AND 9)\n")
    f.write("="*80 + "\n\n")

    for var_name in sorted(complete_vars.keys()):
        f.write(f"  {var_name}\n")

    f.write("\n")
    f.write("="*80 + "\n")
    f.write("VARIABLES ONLY IN FLEXIBLE (MISSING FROM COMPLETE)\n")
    f.write("="*80 + "\n\n")

    only_flexible = set(flexible_vars.keys()) - set(complete_vars.keys())
    if only_flexible:
        for var_name in sorted(only_flexible):
            waves_avail = sorted(flexible_vars[var_name].keys())
            wave_str = ", ".join(map(str, waves_avail))
            f.write(f"  {var_name:<30} (only in waves: {wave_str})\n")
    else:
        f.write("  (none - all flexible variables are complete!)\n")

    f.write("\n")
    f.write("="*80 + "\n")
    f.write("ALTERNATIVES FOUND\n")
    f.write("="*80 + "\n\n")

    if alternatives_found:
        for var, desc in alternatives_found.items():
            f.write(f"  {var}: {desc}\n")
    else:
        f.write("  (none found)\n")

    f.write("\n")
    f.write("="*80 + "\n")
    f.write("RECOMMENDATIONS\n")
    f.write("="*80 + "\n\n")
    f.write("For GEE analysis from your proposal:\n\n")
    f.write("1. If you need teacher variables (mediator analysis):\n")
    f.write("   → Use FLEXIBLE version\n")
    f.write("   → Note: Teacher variables only available waves 2 & 4\n")
    f.write("   → Mediation analysis limited to K-1st grade period\n\n")
    f.write("2. If you want perfectly balanced data across all waves:\n")
    f.write("   → Use COMPLETE version\n")
    f.write("   → All variables have consistent structure 2, 4, 9\n")
    f.write("   → Excludes teacher variables (not in wave 9)\n\n")
    f.write("3. For maximum statistical power:\n")
    f.write("   → Use FLEXIBLE version\n")
    f.write("   → GEE handles missing data well\n")
    f.write("   → More variables available for analysis\n\n")

print(f"  ✓ Saved: {report_file}")
print()