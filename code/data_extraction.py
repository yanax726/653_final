#!/usr/bin/env python3
import pandas as pd
import numpy as np
import re
from pathlib import Path
import warnings
print("Step 1: Discovering available variables in the dictionary...")
print("-"*80)

# Path to dictionary file
dict_file = Path("data/ECLSK2011_K5PUF.dct")

# Check if file exists
if not dict_file.exists():
    print("ERROR: Cannot find dictionary file at data/ECLSK2011_K5PUF.dct")
    exit(1)

# First, let's discover ALL variables in the dictionary
all_dict_variables = {}
current_line_number = 1

with open(dict_file, "r", encoding="latin-1") as f:
    for line in f:
        # Track which of the 27 lines we're reading
        if "_line(" in line:
            match = re.search(r"_line\((\d+)\)", line)
            if match:
                current_line_number = int(match.group(1))
        
        # Extract column specifications
        if "_column(" in line:
            col_match = re.search(r"_column\((\d+)\)", line)
            if col_match:
                col_start = int(col_match.group(1))
                
                # Parse the line to get variable name and type
                parts = line.split()
                col_index = next((i for i, p in enumerate(parts) if "_column" in p), None)
                
                if col_index and len(parts) > col_index + 2:
                    var_type = parts[col_index + 1]
                    var_name = parts[col_index + 2].upper()
                    
                    # Store ALL variables for discovery
                    all_dict_variables[var_name] = {
                        "line": current_line_number,
                        "column": col_start,
                        "type": var_type
                    }

print(f"Total variables in dictionary: {len(all_dict_variables)}")

# These are the patterns we're looking for
needed_patterns = {
    "CHILDID": ["CHILDID"],
    "MATH_SCORES": ["MSCAL", "MTHSCL", "X.*MSCAL.*"],
    "READING_SCORES": ["RSCAL", "RDSCL", "X.*RSCAL.*"],
    "FOOD_SECURITY": ["FS", "FOOD", "X.*FS.*"],
    "TEACHER_BEHAVIOR": ["TCH", "X.*TCH.*"],
    "TEACHER_PERCEPTION": ["ATTN", "INB", "CLSN", "CNFL"],
    "DEMOGRAPHICS": ["CHSEX", "RACE", "AGE", "KAGE", "HPARNT", "FIRKDG"],
    "SES": ["SESL", "SES", "PAR.*ED"],
    "SCHOOL": ["S.*_ID", "PUBPRI", "LOCALE", "FMEAL"],
    "WEIGHTS": ["W[0-9].*"]
}

# Find matching variables
found_variables = {}
for category, patterns in needed_patterns.items():
    found_variables[category] = []
    for var_name in all_dict_variables:
        for pattern in patterns:
            if re.search(pattern, var_name, re.IGNORECASE):
                found_variables[category].append(var_name)
                break

# Print what we found
for category, vars_list in found_variables.items():
    print(f"\n{category}: Found {len(vars_list)} variables")
    if len(vars_list) > 0 and len(vars_list) <= 10:
        for var in sorted(vars_list)[:10]:
            print(f"  - {var}")
    elif len(vars_list) > 10:
        for var in sorted(vars_list)[:5]:
            print(f"  - {var}")
        print(f"  ... and {len(vars_list) - 5} more")

# 3.BUILD EXTRACTION LIST FROM AVAILABLE VARIABLES
# Compile list of variables to extract
variables_to_extract = []

# Always include CHILDID if it exists
if "CHILDID" in all_dict_variables:
    variables_to_extract.append("CHILDID")

# Add all found variables from our patterns
for category, vars_list in found_variables.items():
    variables_to_extract.extend(vars_list)

# Remove duplicates
variables_to_extract = list(set(variables_to_extract))

print(f"Total variables to extract: {len(variables_to_extract)}")

# Build extraction specifications
variable_specs = []
for var_name in variables_to_extract:
    if var_name in all_dict_variables:
        spec = all_dict_variables[var_name]
        var_type = spec["type"]
        
        # Determine data type and width
        if var_type.startswith("str"):
            try:
                width = int(var_type[3:])
            except:
                width = 10
            dtype = "str"
        elif var_type in ["byte", "int", "long"]:
            width = 8
            dtype = "int"
        elif var_type in ["float", "double"]:
            width = 12
            dtype = "float"
        else:
            width = 10
            dtype = "str"
        
        variable_specs.append({
            "name": var_name,
            "line": spec["line"],
            "column": spec["column"],
            "width": width,
            "dtype": dtype
        })

print(f"Prepared {len(variable_specs)} variables for extraction")

# 4. EXTRACT DATA FROM THE .DAT FILE

print("\nStep 4: Extracting data from childK5p.dat...")
print("-"*80)

# Path to data file
data_file = Path("data/childK5p.dat")

# Check if file exists
if not data_file.exists():
    print("ERROR: Cannot find data file at data/childK5p.dat")
    exit(1)

# Read the data file (27 lines per child)
LINES_PER_CHILD = 27
extracted_data = []
current_child_lines = []
child_count = 0

print("Reading data file (this takes 3-5 minutes)...")
print("File size: 2.3 GB")
print()

with open(data_file, "r", encoding="latin-1") as f:
    for line in f:
        # Remove newline and add to current child's lines
        current_child_lines.append(line.rstrip("\n"))
        
        # When we have all 27 lines for one child
        if len(current_child_lines) == LINES_PER_CHILD:
            child_data = {}
            
            # Extract each variable
            for spec in variable_specs:
                line_num = spec["line"] - 1  # Convert to 0-indexed
                col_start = spec["column"] - 1  # Convert to 0-indexed
                col_end = col_start + spec["width"]
                
                # Get the value from the correct line
                try:
                    if line_num < len(current_child_lines):
                        line_text = current_child_lines[line_num]
                        # Make sure line is long enough
                        if len(line_text) > col_start:
                            if len(line_text) >= col_end:
                                raw_value = line_text[col_start:col_end]
                            else:
                                raw_value = line_text[col_start:]
                            raw_value = raw_value.strip()
                        else:
                            raw_value = ""
                        
                        # Convert to appropriate type
                        if spec["dtype"] == "int":
                            if raw_value and raw_value not in ["-9", "-8", "-7", "-1", ""]:
                                try:
                                    child_data[spec["name"]] = int(raw_value)
                                except ValueError:
                                    child_data[spec["name"]] = np.nan
                            else:
                                child_data[spec["name"]] = np.nan
                        elif spec["dtype"] == "float":
                            if raw_value and raw_value not in ["-9", "-8", "-7", "-1", ""]:
                                try:
                                    child_data[spec["name"]] = float(raw_value)
                                except ValueError:
                                    child_data[spec["name"]] = np.nan
                            else:
                                child_data[spec["name"]] = np.nan
                        else:  # string
                            child_data[spec["name"]] = raw_value if raw_value else ""
                    else:
                        child_data[spec["name"]] = np.nan
                        
                except Exception as e:
                    child_data[spec["name"]] = np.nan
            
            # Add this child's data to our list
            extracted_data.append(child_data)
            
            # Reset for next child
            current_child_lines = []
            child_count += 1
            
            # Show progress
            if child_count % 1000 == 0:
                print(f"  Processed {child_count:,} children...", end="\r")
# 5. CREATE DATAFRAME AND HANDLE EXISTING DATA
# Create dataframe from extracted data
df_extracted = pd.DataFrame(extracted_data)
print(f"Extracted data shape: {df_extracted.shape}")

# Check if extraction was successful
if df_extracted.shape[1] == 0:
    print("WARNING: No variables were extracted!")
    print("This might be due to variable name mismatches.")
    print("Creating basic dataset from ECLSData.csv only...")
    
    # Try to use existing data
    existing_file = Path("data/ECLSData.csv")
    if existing_file.exists():
        df_final = pd.read_csv(existing_file)
        print(f"Using existing data: {df_final.shape}")
    else:
        print("ERROR: No data could be extracted and no existing data found!")
        exit(1)
else:
    print(f"Successfully extracted {df_extracted.shape[1]} variables")
    
    # Check if we have existing ECLSData.csv to merge with
    existing_file = Path("data/ECLSData.csv")
    if existing_file.exists():
        print("Found existing ECLSData.csv, merging...")
        
        # Read existing data
        df_existing = pd.read_csv(existing_file)
        print(f"Existing data shape: {df_existing.shape}")
        
        # Check for ID columns
        id_col_extracted = None
        id_col_existing = None
        
        # Find ID column in extracted data
        for col in df_extracted.columns:
            if "CHILDID" in col.upper():
                id_col_extracted = col
                break
        
        # Find ID column in existing data
        for col in df_existing.columns:
            if "CHILDID" in col.upper() or col.lower() == "childid":
                id_col_existing = col
                break
        
        # If we have ID columns in both, merge
        if id_col_extracted and id_col_existing:
            print(f"Merging on {id_col_existing} (existing) and {id_col_extracted} (extracted)")
            
            # Standardize IDs for merging
            df_existing[id_col_existing] = df_existing[id_col_existing].astype(str).str.strip()
            df_extracted[id_col_extracted] = df_extracted[id_col_extracted].astype(str).str.strip()
            
            # Remove duplicate columns before merging (except ID)
            existing_cols = set(df_existing.columns.str.upper())
            extracted_cols = set(df_extracted.columns.str.upper())
            
            # Find duplicates (case-insensitive)
            cols_to_drop = []
            for col in df_extracted.columns:
                if col.upper() in existing_cols and col.upper() != id_col_extracted.upper():
                    cols_to_drop.append(col)
            
            if cols_to_drop:
                print(f"Removing {len(cols_to_drop)} duplicate columns from extracted data")
                df_extracted = df_extracted.drop(columns=cols_to_drop)
            
            # Merge the datasets
            df_final = df_existing.merge(
                df_extracted,
                left_on=id_col_existing,
                right_on=id_col_extracted,
                how="left"
            )
            
            # Remove duplicate ID column if created
            if id_col_extracted != id_col_existing and id_col_extracted in df_final.columns:
                df_final = df_final.drop(columns=[id_col_extracted])
            
            print(f"Merged data shape: {df_final.shape}")
        else:
            print("No common ID column found, using existing data only")
            df_final = df_existing
    else:
        print("No existing data found, using extracted data only")
        df_final = df_extracted


# 6. QUALITY CHECKS
# List all columns for reference
print("Sample of available columns:")
for i, col in enumerate(sorted(df_final.columns)[:20]):
    print(f"  - {col}")
if len(df_final.columns) > 20:
    print(f"  ... and {len(df_final.columns) - 20} more")

# Check for key variable patterns
print("\nChecking for key variable types:")

# Academic variables
math_vars = [col for col in df_final.columns if "MSCAL" in col.upper() or "MATH" in col.upper()]
reading_vars = [col for col in df_final.columns if "RSCAL" in col.upper() or "READ" in col.upper()]
print(f"  Math variables: {len(math_vars)}")
print(f"  Reading variables: {len(reading_vars)}")

# Food security
fs_vars = [col for col in df_final.columns if "FS" in col.upper() and "X" in col.upper()]
print(f"  Food security variables: {len(fs_vars)}")

# Teacher variables
teacher_vars = [col for col in df_final.columns if "TCH" in col.upper()]
print(f"  Teacher-related variables: {len(teacher_vars)}")

# Sample size
print(f"\nTotal sample size: {len(df_final):,}")

# Create output directory if it doesn't exist
output_dir = Path("data_processed")
output_dir.mkdir(exist_ok=True)

# Save the complete dataset
output_file = output_dir / "ecls_complete_for_analysis.csv"
df_final.to_csv(output_file, index=False)

print(f"✓ Saved final dataset to: {output_file}")
print(f"  Shape: {df_final.shape[0]:,} rows × {df_final.shape[1]} columns")
print()

# Save a data dictionary for reference
dict_file = output_dir / "available_variables.txt"
with open(dict_file, "w") as f:
    f.write("ECLS-K AVAILABLE VARIABLES\n")
    f.write("="*60 + "\n\n")
    f.write(f"Total variables: {len(df_final.columns)}\n")
    f.write(f"Total observations: {len(df_final):,}\n\n")
    
    f.write("ALL VARIABLES:\n")
    f.write("-"*30 + "\n")
    for col in sorted(df_final.columns):
        non_missing = df_final[col].notna().sum()
        pct_complete = (non_missing / len(df_final)) * 100
        f.write(f"{col:<30} ({non_missing:,} values, {pct_complete:.1f}% complete)\n")

print(f"✓ Saved variable list to: {dict_file}")
print()
