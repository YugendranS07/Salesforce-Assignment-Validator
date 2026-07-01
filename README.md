# Salesforce Assignment Validator

**Automated validation of Salesforce Permission Set and Public Group assignments — replacing hours of manual org checking with a single script run.**

---

## The Problem

When the business team requests that a set of users be given specific access in Salesforce — Permission Sets, Public Groups, or both — someone has to go into the org and confirm that every single assignment actually landed correctly.

Before this tool, that meant doing it by hand:

1. Receive a spreadsheet from the business listing users and the access they should have.
2. Log in to Salesforce.
3. Go to **Setup → Users**, open each user one at a time.
4. Scroll to **Permission Set Assignments** (or **Public Groups**) and visually check each item on the list.
5. Note down what matched and what didn't.
6. Move to the next user. Repeat for every user × every permission set/group.

### Why this was painful

| Pain Point | Reality |
|---|---|
| Scale | 50 users × 20 permission sets = 1,000 individual manual checks |
| Human error | Easy to misread a checkbox or skip a row |
| Time | Hours, sometimes days, for a single validation request |
| No audit trail | Nothing documented — just someone's word that it was checked |
| Repetitive | The exact same process every time a new request came in |
| Not scalable | Every additional user makes the job proportionally worse |

This kind of manual, row-by-row reconciliation is exactly the sort of task that's fast for a computer and slow and error-prone for a person.

---

## The Solution

This tool takes two inputs and produces one audit-ready Excel report:

1. **Source file** — submitted by the business, listing each user and which Permission Sets / Public Groups they are *expected* to have (`TRUE`/`FALSE` per column).
2. **Org data export** — pulled from Salesforce (e.g. via a SOQL query on `PermissionSetAssignment` or `GroupMember`), listing what is *actually* assigned in the org.

The script compares the two, flags every mismatch, and writes out a timestamped Excel report with a summary, a full comparison, and a failures-only view — in seconds, with zero manual clicking.

It was originally built for **Permission Sets** and has been generalized to also validate **Public Group** membership, since both problems are structurally identical: *"does the org actually reflect what the business asked for?"*

### Before vs. After

| Aspect | Before (Manual) | After (Automated) |
|---|---|---|
| Time per user | 15–30 minutes | Milliseconds |
| 50-user validation | 1–2 days | Under 10 seconds |
| Human error | High risk | Eliminated — logic is deterministic |
| Audit trail | None | Timestamped Excel report, every run |
| Scalability | Breaks down with volume | Handles thousands of rows |
| Repeatability | Tedious every time | Re-run the script |
| Applies to | Permission Sets only (manual) | Permission Sets **and** Public Groups |

---

## How It Works

1. **Load inputs** — the source file is read as-is; the org export (which may contain multiple sheets, e.g. one per export batch) is loaded and merged into a single table.
2. **Normalize** — all IDs and assignment names are trimmed, upper-cased, and stripped of stray whitespace/non-breaking spaces so formatting differences never cause a false mismatch.
3. **Melt the source** — the wide source table (one column per permission set/group) is reshaped into a long table: one row per `(User, Assignment)` pair, which is what actually needs to be checked.
4. **Cross-check against the org export** — for every `(User, Assignment)` pair from the source, the script checks whether that pair exists in the Salesforce export.
5. **Match logic**:
   - Source says **assign** (`TRUE`) → and it **is** present in the org → ✅ Match
   - Source says **don't assign** (`FALSE`) → and it is **not** present in the org → ✅ Match
   - Anything else → ❌ Mismatch, flagged for review
6. **Report** — three sheets are written to a single timestamped `.xlsx` file:

   | Sheet | Contents |
   |---|---|
   | `Summary` | Per-assignment totals: Total checked, Matched, Failed, Pass/Fail outcome |
   | `Comparison` | Every single check performed, for all users and all assignments |
   | `Failed` | Only the mismatches, with plain-English labels (`Assign`/`Don't Assign`, `Assigned`/`Not Assigned`) |

   If a sheet would exceed Excel's 1,048,576-row limit, it's automatically split across multiple sheets.

---

## Repository Structure

```
salesforce-assignment-validator/
├── src/
│   └── validate_assignments.py   # Main script (CLI)
├── sample_data/
│   ├── Source_User_Test.xlsx     # Example business source file
│   ├── Orgdata_User.xlsx         # Example Salesforce org export
│   └── sample_output/
│       └── comparison_output_sample.xlsx   # Example generated report
├── requirements.txt
├── LICENSE
├── .gitignore
└── README.md
```

---

## Getting Started

### Requirements

- Python 3.9+
- `pandas`, `openpyxl`

```bash
pip install -r requirements.txt
```

### Usage

```bash
python src/validate_assignments.py \
  --source path/to/Source_User_Test.xlsx \
  --org path/to/Orgdata_User.xlsx \
  --type permission_set
```

To validate **Public Group** membership instead, just change `--type`:

```bash
python src/validate_assignments.py \
  --source path/to/Source_User_Test.xlsx \
  --org path/to/Orgdata_User.xlsx \
  --type public_group
```

| Flag | Required | Description |
|---|---|---|
| `--source` | Yes | Path to the business-submitted expected-assignment file |
| `--org` | Yes | Path to the Salesforce org data export |
| `--type` | No | `permission_set` (default) or `public_group` — controls the expected org column name |
| `--assignment-column` | No | Override the org export column name directly (if it doesn't match the default for `--type`) |
| `--output` | No | Custom output filename (default: `comparison_output_<type>_<timestamp>.xlsx`) |

Try it immediately against the included sample data:

```bash
python src/validate_assignments.py \
  --source sample_data/Source_User_Test.xlsx \
  --org sample_data/Orgdata_User.xlsx \
  --type permission_set
```

---

## Input File Requirements

### Source file (business expectation)

- Must contain a user ID column named `Source ID`, `SourceID`, or `ID`.
- Every other column is treated as one Permission Set or Public Group.
- Cell values indicate intent: `TRUE`/`FALSE`, `Y`/`N`, `1`/`0`, `YES`/`NO`.

| Source ID | Sales_Cloud_User | Finance_Read_Only | Marketing_Admin |
|---|---|---|---|
| U001 | TRUE | FALSE | TRUE |
| U002 | TRUE | TRUE | FALSE |

### Org data export

- Same user ID column as the source file.
- A column holding the assignment name:
  - `PermissionSet.Name` for `--type permission_set` (e.g. from a SOQL query on `PermissionSetAssignment`)
  - `Group.Name` for `--type public_group` (e.g. from a SOQL query on `GroupMember`)
- Multiple sheets are supported and merged automatically (useful for batched exports).

| Source ID | PermissionSet.Name |
|---|---|
| U001 | Sales_Cloud_User |
| U001 | Marketing_Admin |
| U002 | Sales_Cloud_User |

---

## Sample Output

Running the script on the included sample data produces `comparison_output_sample.xlsx` with:

- **Summary**: 4 permission sets checked, 2 with failures flagged.
- **Comparison**: all 20 user/permission-set checks with their match status.
- **Failed**: the 2 specific mismatches, e.g. a permission set the business said *not* to assign that was found assigned in the org.

See [`sample_data/sample_output/comparison_output_sample.xlsx`](sample_data/sample_output/comparison_output_sample.xlsx) for the full example.

---

## Roadmap Ideas

- [ ] Extend to Profile validation
- [ ] Extend to Queue membership validation
- [ ] Direct Salesforce API/SOQL pull instead of a manually exported file
- [ ] HTML/dashboard-style report in addition to Excel

---

## License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for details.

## Related

Companion project: [Excel-Comparison-Tool](https://github.com/YugendranS07/Excel-Comparison-Tool/tree/main)
