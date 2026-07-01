<div align="center">

# 🛡️ Salesforce Assignment Validator

### Stop clicking through user profiles one by one. Let Python do the audit.

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![License](https://img.shields.io/badge/License-MIT-2ECC71?style=for-the-badge)](LICENSE)
[![Salesforce](https://img.shields.io/badge/Salesforce-Permission%20Sets%20%7C%20Public%20Groups-00A1E0?style=for-the-badge&logo=salesforce&logoColor=white)](#)
[![Status](https://img.shields.io/badge/Status-Active-orange?style=for-the-badge)](#)

**Compares what the business *asked for* against what Salesforce *actually has* — and hands you a clean, color-coded audit report in seconds.**

</div>

---

## 🚨 The Problem

Picture this: the business team sends a spreadsheet asking for **50 users** to get **20 different Permission Sets**. That's **1,000 individual checks** — and until now, someone had to do this by hand:

```
1. Open the spreadsheet from the business  📄
2. Log in to Salesforce                    🔑
3. Setup → Users → open each user           🧍
4. Scroll through Permission Set Assignments 🔍
5. Eyeball each one: assigned or not?        👀
6. Repeat... 999 more times                  😵‍💫
```

| 🚩 Pain Point | 😖 Reality |
|:---|:---|
| **Scale** | 50 users × 20 permission sets = 1,000 manual checks |
| **Human error** | One missed checkbox = a security gap that goes unnoticed |
| **Time** | Hours — sometimes days — for a single validation request |
| **Audit trail** | None. Just someone's word that "it was checked" |
| **Repeatability** | Same painful process, every single time |
| **Scalability** | Gets worse with every new user added |

---

## ✅ The Solution

Give the script **two files**, get back **one report**:

```
📥  Source file  (what the business expects)
       +
📥  Org export   (what Salesforce actually has)
       ↓
🐍  validate_assignments.py
       ↓
📊  comparison_output.xlsx   →   Summary · Comparison · Failed
```

Originally built to validate **Permission Sets**, the tool now works identically for **Public Group** membership — same logic, same speed, same audit trail. Just flip one flag.

### ⚡ Before vs. After

| | 🐌 Before (Manual) | 🚀 After (Automated) |
|:---|:---|:---|
| Time per user | 15–30 minutes | Milliseconds |
| 50-user validation | 1–2 days | Under 10 seconds |
| Human error | High risk | Eliminated |
| Audit trail | None | Timestamped Excel report |
| Scale | Breaks down | Handles thousands of rows |
| Coverage | Permission Sets only | Permission Sets **+** Public Groups |

---

## 🧠 How It Works

| Step | What Happens |
|:---:|:---|
| **1️⃣ Load** | Reads the source file and merges every sheet of the (possibly multi-batch) org export |
| **2️⃣ Normalize** | Strips whitespace, casing, and hidden characters so formatting quirks never cause a false mismatch |
| **3️⃣ Melt** | Reshapes the wide source table into one row per `(User, Assignment)` pair |
| **4️⃣ Cross-check** | Looks up each pair against the actual Salesforce export |
| **5️⃣ Match logic** | ✅ `TRUE` + present → match  •  ✅ `FALSE` + absent → match  •  ❌ anything else → flagged |
| **6️⃣ Report** | Writes a 3-tab Excel workbook: `Summary`, `Comparison`, `Failed` |

---

## 📁 Repository Structure

```
salesforce-assignment-validator/
├── 🐍 src/
│   └── validate_assignments.py       ← the script
├── 📊 sample_data/
│   ├── Source_User_Test.xlsx         ← example business request
│   ├── Orgdata_User.xlsx             ← example org export
│   └── sample_output/
│       └── comparison_output_sample.xlsx
├── 📄 requirements.txt
├── ⚖️  LICENSE
├── 🚫 .gitignore
└── 📖 README.md
```

---

## 🏁 Getting Started

### Install

```bash
pip install -r requirements.txt
```

### Run — Permission Sets 🔐

```bash
python src/validate_assignments.py \
  --source sample_data/Source_User_Test.xlsx \
  --org sample_data/Orgdata_User.xlsx \
  --type permission_set
```

### Run — Public Groups 👥

```bash
python src/validate_assignments.py \
  --source sample_data/Source_User_Test.xlsx \
  --org sample_data/Orgdata_User.xlsx \
  --type public_group
```

### ⚙️ CLI Options

| Flag | Required | Description |
|:---|:---:|:---|
| `--source` | ✅ | Business-submitted expected-assignment file |
| `--org` | ✅ | Salesforce org data export |
| `--type` | ⬜ | `permission_set` (default) or `public_group` |
| `--assignment-column` | ⬜ | Override the org column name if it's non-standard |
| `--output` | ⬜ | Custom output filename |

---

## 📋 Input File Requirements

### 📥 Source file (business expectation)

- One user ID column: `Source ID`, `SourceID`, or `ID`
- Every other column = one Permission Set / Public Group
- Cell values: `TRUE`/`FALSE`, `Y`/`N`, `1`/`0`, `YES`/`NO`

| Source ID | Sales Cloud User | Finance Read Only | Marketing Admin |
|:---:|:---:|:---:|:---:|
| U001 | 🟢 TRUE | 🔴 FALSE | 🟢 TRUE |
| U002 | 🟢 TRUE | 🟢 TRUE | 🔴 FALSE |

### 📥 Org data export

- Same user ID column
- Assignment name column: `PermissionSet.Name` (permission sets) or `Group.Name` (public groups)
- Multiple sheets supported — automatically merged

| Source ID | PermissionSet.Name |
|:---:|:---|
| U001 | Sales Cloud User |
| U001 | Marketing Admin |
| U002 | Sales Cloud User |

---

## 📊 Sample Output

Running the script on the included sample data produces a 3-tab report:

| Tab | 🎯 Purpose |
|:---|:---|
| 🟩 **Summary** | Per-assignment totals — Total / Matched / Failed / Pass or Fail |
| 🟦 **Comparison** | Every single check, for every user and assignment |
| 🟥 **Failed** | Only the mismatches, in plain English (`Assign` / `Don't Assign`, `Assigned` / `Not Assigned`) |

👉 See it live: [`sample_data/sample_output/comparison_output_sample.xlsx`](sample_data/sample_output/comparison_output_sample.xlsx)

---

## 🗺️ Roadmap

- [ ] 👤 Extend to Profile validation
- [ ] 📬 Extend to Queue membership validation
- [ ] 🔌 Pull directly from Salesforce via API/SOQL instead of a manual export
- [ ] 📈 Optional HTML/dashboard-style report alongside Excel

---

## ⚖️ License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

## 🔗 Related

Companion project: [**Excel-Comparison-Tool**](https://github.com/YugendranS07/Excel-Comparison-Tool/tree/main)

---

<div align="center">

Made to save someone's afternoon of clicking through user records. 🙌

</div>
