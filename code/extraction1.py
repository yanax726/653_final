#!/usr/bin/env python3
"""
FINAL ECLS-K EXTRACTION
"""

import pandas as pd
import re
from collections import defaultdict
from pathlib import Path

# --- FOOD SECURITY (adult + child, Waves 2,4,7,8,9) ---
FOOD_SECURITY_VARS = [
    # Wave 2 (Spring K)
    "X2FSRAW2", "X2FSSCAL2", "X2FSSTAT2",
    "X2FSADRA2", "X2FSADSC2", "X2FSADST2",
    "X2FSCHRA", "X2FSCHSC", "X2FSCHST",
    # Wave 4 (Spring 1st)
    "X4FSRAW2", "X4FSSCAL2", "X4FSSTAT2",
    "X4FSADRA2", "X4FSADSC2", "X4FSADST2",
    "X4FSCHRA", "X4FSCHSC", "X4FSCHST",
    # Waves 7–8 (adult only)
    "X7FSADRA2", "X7FSADSC2", "X7FSADST2",
    "X8FSADRA2", "X8FSADSC2", "X8FSADST2",
    # Wave 9 (Spring 5th; adult + child)
    "X9FSRAW2", "X9FSSCAL2", "X9FSSTAT2",
    "X9FSADRA2", "X9FSADSC2", "X9FSADST2",
    "X9FSCHRA", "X9FSCHSC", "X9FSCHST",
]

# --- TEACHER SOCIOEMOTIONAL SCALES (behavior) ---
TEACHER_BEHAVIOR_VARS = [
    # Approaches to learning, externalizing, internalizing, self-control etc.
    # (These are already in ECLSData but we include them for completeness;
    #  duplicates will be removed before merge.)
    "X1TCHCON", "X2TCHCON", "X4TCHCON", "X6TCHCON",
    "X1TCHAPP", "X2TCHAPP", "X4TCHAPP", "X6TCHAPP",
    "X1TCHEXT", "X2TCHEXT", "X4TCHEXT", "X6TCHEXT",
    "X1TCHINT", "X2TCHINT", "X4TCHINT", "X6TCHINT",
]

# --- MEDIATOR CANDIDATES: TEACHER RELATIONSHIP & PERCEPTIONS ---
# (brainstorm slides used TCLOSU/TCONFL; in the actual data these are
#  stored as CLOSENESS / CONFLICT composites and TMCQ-like scales)
TEACHER_RELATIONSHIP_VARS = [
    # Closeness composites
    "X2CLSNSS", "X4CLSNSS", "X6CLSNSS", "X7CLSNSS",
    # Conflict composites
    "X2CNFLCT", "X4CNFLCT", "X6CNFLCT", "X7CNFLCT",
]

TEACHER_PERCEPTION_VARS = [
    # Attentional focus (teacher report)
    "X1ATTNFS", "X2ATTNFS", "X4ATTNFS", "X4KATTNFS",
    # Inhibitory control (teacher report)
    "X1INBCNT", "X2INBCNT", "X4INBCNT", "X4KINBCNT",
    # Later TMCQ versions (5th grade; optional but harmless)
    "X9ATTMCQ", "X9INTMCQ",
]

# --- DEMOGRAPHICS AND COVARIATES ---
COVARIATE_VARS = [
    "CHILDID",
    "PARENTID",
    "PSUID",
    "S1_ID", "S2_ID", "S3_ID", "S4_ID", "S5_ID", "S6_ID", "S7_ID", "S8_ID", "S9_ID",
    "X_CHSEX_R",
    "X_RACETHP_R",
    "X1KAGE_R", "X2KAGE_R",
    "X1FIRKDG",        # X2FIRKDG does NOT exist in the dictionary
    "X1HPARNT", "X2HPARNT", "X4HPARNT", "X6HPARNT", "X7HPARNT",
]

# --- SAMPLING WEIGHTS ---
WEIGHT_VARS = [
    "W1C0", "W1P0", "W2P0", "W12P0",
    "W4CF4P_20", "W6CS6P_20", "W7C7P_20", "W9C9P_20",  # note: W9C9P_20 (not _90)
]

# --- OPTIONAL: SCIENCE SCALE SCORES (if you decide to use them later) ---
SCIENCE_VARS = [
    "X2SSCALK5", "X4SSCALK5", "X6SSCALK5", "X7SSCALK5", "X8SSCALK5", "X9SSCALK5",
]

REQUIRED_VARS = (
    FOOD_SECURITY_VARS
    + TEACHER_BEHAVIOR_VARS
    + TEACHER_RELATIONSHIP_VARS
    + TEACHER_PERCEPTION_VARS
    + COVARIATE_VARS
    + WEIGHT_VARS
    + SCIENCE_VARS
)

REQUIRED_VARS = sorted(set(REQUIRED_VARS))  # unique, sorted

#  PARSE THE .DCT FILE INTO A FULL COLUMN MAP
dct_file = Path("data/ECLSK2011_K5PUF.dct")
if not dct_file.exists():
    raise FileNotFoundError(f"Cannot find {dct_file}")

# First pass: collect all columns with line, start position, Stata type, and name
all_cols = []  # list of dicts: {name, line, col, vtype}
current_line = 1

with open(dct_file, "r", encoding="latin-1", errors="replace") as f:
    for raw in f:
        line = raw.strip()
        # detect which physical line within 27-line record we're in
        m_line = re.search(r"_line\((\d+)\)", line)
        if m_line:
            current_line = int(m_line.group(1))
            continue

        m_col = re.search(r"_column\((\d+)\)", line)
        if not m_col:
            continue

        col_start = int(m_col.group(1))
        parts = raw.split()
        # pattern: _column(col) <type> <name> <format> "label"
        try:
            col_idx = next(i for i, p in enumerate(parts) if "_column" in p)
        except StopIteration:
            continue

        if len(parts) <= col_idx + 2:
            continue

        vtype = parts[col_idx + 1]   # e.g., "double", "long", "str8"
        vname = parts[col_idx + 2]   # e.g., "X2FSSCAL2"

        all_cols.append(
            {
                "name": vname.upper(),
                "line": current_line,
                "col": col_start,
                "vtype": vtype.lower(),
            }
        )

from collections import defaultdict
cols_by_line = defaultdict(list)
for spec in all_cols:
    cols_by_line[spec["line"]].append(spec)

# Second pass: within each line, sort by column and compute effective width
for line_num, specs in cols_by_line.items():
    specs.sort(key=lambda d: d["col"])
    for i, spec in enumerate(specs):
        if i < len(specs) - 1:
            width = specs[i + 1]["col"] - spec["col"]
        else:
            # last column on the line: just give it a generous width
            # (strip() before parsing, so trailing spaces are harmless)
            width = 20
        spec["width"] = width

# Now build a lookup dict ONLY for required variables
var_specs = []
for spec in all_cols:
    if spec["name"] in REQUIRED_VARS:
        # attach width computed above
        line_specs = cols_by_line[spec["line"]]
        # find same object to read width safely
        for ls in line_specs:
            if ls["name"] == spec["name"] and ls["col"] == spec["col"]:
                width = ls["width"]
                break
        else:
            width = 20

        # map Stata type to simple dtype
        vtype = spec["vtype"]
        if vtype.startswith("str"):
            dtype = "str"
        elif vtype in {"byte", "int", "long"}:
            dtype = "int"
        elif vtype in {"float", "double"}:
            dtype = "float"
        else:
            dtype = "str"

        var_specs.append(
            {
                "name": spec["name"],
                "line": spec["line"],
                "col": spec["col"],
                "width": width,
                "dtype": dtype,
            }
        )

found_names = sorted({v["name"] for v in var_specs})
missing = sorted(set(REQUIRED_VARS) - set(found_names))

print(f"✓ Found {len(found_names)} of {len(REQUIRED_VARS)} requested variables")
if missing:
    print("\n⚠️  Variables requested but NOT found in .dct:")
    for v in missing:
        print(f"    {v}")
    print("  (These will simply be omitted from extraction.)")
print()

dat_file = Path("data/childK5p.dat")
if not dat_file.exists():
    raise FileNotFoundError(f"Cannot find {dat_file}")

print("Processing ~2.3 GB multi-line .dat file (27 lines per child)...")
print()

data_rows = []
current_record = []

with open(dat_file, "r", encoding="latin-1", errors="replace") as f:
    for raw_line in f:
        current_record.append(raw_line.rstrip("\n"))

        if len(current_record) == LINE_COUNT:
            row = {}
            for spec in var_specs:
                line_idx = spec["line"] - 1  # 1-based in .dct
                col_start = spec["col"] - 1  # 1-based in .dct
                col_end = col_start + spec["width"]

                try:
                    line_text = current_record[line_idx]
                except IndexError:
                    value_str = ""
                else:
                    value_str = line_text[col_start:col_end].strip()

                if spec["dtype"] == "int":
                    if value_str == "" or value_str in {"-9", "-8", "-7", "-4", "-3", "-2", "-1"}:
                        val = None
                    else:
                        try:
                            val = int(value_str)
                        except ValueError:
                            val = None
                elif spec["dtype"] == "float":
                    if value_str == "" or value_str in {"-9", "-8", "-7", "-4", "-3", "-2", "-1"}:
                        val = None
                    else:
                        try:
                            val = float(value_str)
                        except ValueError:
                            val = None
                else:
                    # string
                    val = value_str if value_str != "" else None

                row[spec["name"]] = val

            data_rows.append(row)
            current_record = []

            if len(data_rows) % 1000 == 0:
                print(f"  {len(data_rows):,} children processed...", end="\r")

print(f"\n✓ Extracted {len(data_rows):,} children")
print()

# SAVE NEW VARIABLES AND MERGE WITH EXISTING ECLSData.csv
df_new = pd.DataFrame(data_rows)

# Basic sanity checks (dimensions, obvious ranges)
print(f"New variable frame: {df_new.shape[0]:,} rows × {df_new.shape[1]} columns")
if "CHILDID" not in df_new.columns:
    raise RuntimeError("CHILDID is missing from the newly extracted data; cannot merge.")

# Save all newly extracted variables (for inspection)
df_new.to_csv("data/ecls_all_missing_vars.csv", index=False)
print("✓ Saved: data/ecls_all_missing_vars.csv (raw extracted variables)")

# Read existing analytic dataset
existing_path = Path("data/ECLSData.csv")
if not existing_path.exists():
    raise FileNotFoundError("Expected data/ECLSData.csv to exist for merging.")

df_existing = pd.read_csv(existing_path)

# Normalize IDs: strip leading/trailing spaces and force string
df_existing["childid"] = df_existing["childid"].astype(str).str.strip()
df_new["CHILDID"] = df_new["CHILDID"].astype(str).str.strip()

# Drop any columns from df_new that already exist in df_existing (aside from ID)
existing_lower = {c.lower() for c in df_existing.columns}
cols_to_drop = [
    c for c in df_new.columns
    if c.lower() in existing_lower and c.upper() not in {"CHILDID"}
]
if cols_to_drop:
    print("Dropping duplicated variables from new extraction (already in ECLSData.csv):")
    for c in cols_to_drop:
        print(f"  - {c}")
    df_new = df_new.drop(columns=cols_to_drop)

# Merge (left join on existing dataset; do not drop any children already in ECLSData)
df_complete = df_existing.merge(
    df_new,
    left_on="childid",
    right_on="CHILDID",
    how="left",
    validate="1:1",
)

output_path = Path("data_processed")
output_path.mkdir(exist_ok=True, parents=True)
output_file = output_path / "ecls_complete_final.csv"
df_complete.to_csv(output_file, index=False)

print(f"✓ Complete dataset: {df_complete.shape[0]:,} rows × {df_complete.shape[1]} columns")
print(f"✓ Saved: {output_file}")
print()
