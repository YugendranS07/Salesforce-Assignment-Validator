"""
Salesforce Assignment Validator
--------------------------------
Compares a business-submitted "expected assignment" file against an actual
Salesforce org data export to validate whether Permission Sets (or Public
Groups) are correctly assigned to users.

Usage:
    python validate_assignments.py --source Source_User_Test.xlsx --org Orgdata_User.xlsx --type permission_set
    python validate_assignments.py --source Source_User_Test.xlsx --org Orgdata_User.xlsx --type public_group

Author: Yugendran S
"""

import argparse
import datetime
import sys

import pandas as pd

MAX_ROWS = 1_048_576

# Maps the --type flag to the column name expected in the org export file
ASSIGNMENT_TYPE_COLUMNS = {
    "permission_set": "PermissionSet.Name",
    "public_group": "Group.Name",
}


def norm(x):
    """Normalize a value for robust, whitespace/case-insensitive matching."""
    return str(x).strip().upper().replace("\xa0", "").replace(" ", "").replace("\t", "")


def map_source_assignment(val):
    val_clean = str(val).strip().upper()
    if val_clean in {"TRUE", "1", "YES", "Y"}:
        return "Assign"
    return "Don't Assign"


def write_df_multi(df, writer, base_name):
    """Write a dataframe to Excel, splitting across sheets if it exceeds the row limit."""
    n = len(df)
    if n <= MAX_ROWS:
        df.to_excel(writer, sheet_name=base_name, index=False)
    else:
        for i, start in enumerate(range(0, n, MAX_ROWS), start=1):
            end = start + MAX_ROWS
            sheet_name = f"{base_name}_{i}" if i > 1 else base_name
            df.iloc[start:end].to_excel(writer, sheet_name=sheet_name, index=False)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate Salesforce Permission Set / Public Group assignments "
        "against a business-submitted expected assignment file."
    )
    parser.add_argument("--source", required=True, help="Path to the business source file (expected assignments)")
    parser.add_argument("--org", required=True, help="Path to the Salesforce org data export file")
    parser.add_argument(
        "--type",
        choices=ASSIGNMENT_TYPE_COLUMNS.keys(),
        default="permission_set",
        help="What is being validated: 'permission_set' or 'public_group' (default: permission_set)",
    )
    parser.add_argument(
        "--assignment-column",
        default=None,
        help="Override the org export column name that holds the assignment name "
        "(defaults based on --type, e.g. 'PermissionSet.Name' or 'Group.Name')",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file name (default: comparison_output_<type>_<timestamp>.xlsx)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    assignment_col = args.assignment_column or ASSIGNMENT_TYPE_COLUMNS[args.type]

    # --- Load source (business expectation) file ---
    source = pd.read_excel(args.source, dtype=str, header=0)
    orig_source_cols = source.columns.tolist()

    # --- Load and combine all sheets of the org data export ---
    org_sheets = pd.read_excel(args.org, dtype=str, sheet_name=None)
    org = pd.concat(org_sheets.values(), ignore_index=True)

    possible_id_columns = ["Source ID", "SourceID", "ID"]
    id_col = next((col for col in possible_id_columns if col in orig_source_cols), None)
    if not id_col:
        sys.exit(f"ERROR: No ID column found in source file. Columns present: {list(source.columns)}")

    if assignment_col not in org.columns:
        sys.exit(
            f"ERROR: '{assignment_col}' column not found in org export. "
            f"Columns present: {list(org.columns)}"
        )

    assignment_cols = [c for c in orig_source_cols if c != id_col]

    # --- Normalize org data for matching ---
    norm_org = org.copy()
    norm_org[id_col] = norm_org[id_col].astype(str).map(norm)
    norm_org[assignment_col] = norm_org[assignment_col].astype(str).map(norm)

    norm_source_ids = set(source[id_col].astype(str).map(norm))
    norm_org = norm_org[norm_org[id_col].isin(norm_source_ids)]

    # --- Melt source: wide -> long (one row per user/assignment pair) ---
    melted = source.melt(
        id_vars=[id_col],
        value_vars=assignment_cols,
        var_name=assignment_col,
        value_name="Source_value",
    )
    melted["norm_id"] = melted[id_col].map(norm)
    melted["norm_assignment"] = melted[assignment_col].map(norm)
    melted["norm_source_value"] = melted["Source_value"].astype(str).map(norm)

    org_pairs = set(zip(norm_org[id_col], norm_org[assignment_col]))
    melted["Org_present"] = melted.apply(
        lambda row: (row["norm_id"], row["norm_assignment"]) in org_pairs, axis=1
    )

    def is_match(row):
        if row["norm_source_value"] == "TRUE" and row["Org_present"]:
            return True
        if row["norm_source_value"] == "FALSE" and not row["Org_present"]:
            return True
        return False

    melted["Match"] = melted.apply(is_match, axis=1)

    output_cols = [id_col, assignment_col, "Source_value", "Org_present", "Match"]
    melted_out = melted[output_cols].copy()

    # --- Failed rows, human-readable labels ---
    failed = melted_out[~melted_out["Match"]].copy()
    failed = failed.rename(columns={"Source_value": "Source Assignment", "Org_present": "Org Assignment"})
    failed["Source Assignment"] = failed["Source Assignment"].apply(map_source_assignment)
    failed["Org Assignment"] = failed["Org Assignment"].replace({True: "Assigned", False: "Not Assigned"})

    # --- Summary ---
    summary = (
        melted.groupby(assignment_col)["Match"]
        .agg(["count", "sum"])
        .reset_index()
        .rename(columns={"count": "Total", "sum": "Matched"})
    )
    summary["Failed"] = summary["Total"] - summary["Matched"]
    summary["Outcome"] = summary["Failed"].apply(lambda x: "Pass" if x == 0 else "Fail")

    now = datetime.datetime.now()
    output_filename = args.output or f"comparison_output_{args.type}_{now.strftime('%Y%m%d_%H%M%S')}.xlsx"

    with pd.ExcelWriter(output_filename) as writer:
        summary.to_excel(writer, sheet_name="Summary", index=False)
        write_df_multi(melted_out, writer, "Comparison")
        write_df_multi(failed, writer, "Failed")

    print(f"Validation complete. Report saved to '{output_filename}'")
    print(f"  Total checks: {len(melted_out)}  |  Failed: {(~melted_out['Match']).sum()}")


if __name__ == "__main__":
    main()
