import pandas as pd
import numpy as np
import re
import os

# ==========================================================
# VOC REFERENCE LIST
# ==========================================================

VOC_REFERENCE = [

    ("Acetone", 0.46, 43, 0.04),
    ("2- Butanone", 1.01, 43, 0.04),
    ("2- Pentanone", 1.31, 43, 0.04),
    ("4-methyl-2-pentanone", 2.01, 63, 0.04),
    ("pyrrole", 2.09, 67, 0.04),
    ("Toluene", 2.31, 91, 0.04),
    ("3-Hexanone", 2.37, 71, 0.04),
    ("4-Heptanone", 4.19, 71, 0.04),

    ("2-Heptanone", 4.42, 58, 0.05),

    ("1-butene,4-isothiocyanate", 6.59, 72, 0.04),

    ("2-octanone", 7.46, 43, 0.04),

    ("3-Octen-2-one", 9.18, 111, 0.04),

    ("2-ethylhexan-1-ol", 9.19, 57, 0.04),

    ("p-cresol", 10.31, 108, 0.04),

    ("3,7-Dimethylocta-1,6-dien-3-ol (Linalool)", 11.29, 69, 0.05),

    ("Cyclohexanol,5-methyl-2-(1-methylethyl)", 13.37, 81, 0.05),

    ("2,5,-Dimethylbenzaldehyde", 14.19, 133, 0.04),

    ("Benzaldehyde,4-(1-methylethyl)-", 15.03, 133, 0.04),

    ("Carvone (2-methyl-5-(prop-1-en-2-yl)cyclohex-2-en-1-one)", 15.10, 82, 0.05),

    ("2-cyclohexen-1-one,3-methyl-6-(1-methylethyl)-", 15.25, 82, 0.04),

    ("Propane, 1-isothiocyanato-3-(methylthio)", 16.24, 101, 0.05),

    ("Erucin", 19.21, 115, 0.07)

]

# ==========================================================
# RETENTION TIME PARSER
# ==========================================================

def parse_raw_rt(value):

    if pd.isna(value):
        return np.nan

    if isinstance(value, pd.Timestamp):

        h = value.hour
        m = value.minute
        s = value.second

        return h + m/100 + s/10000

    text = str(value).strip().replace(" ", "")

    if text == "":
        return np.nan

    match = re.match(
        r"^(\d+):(\d{1,2}):(\d{1,2}(?:\.\d+)?)$",
        text
    )

    if match:

        h = int(match.group(1))
        m = int(match.group(2))
        s = float(match.group(3))

        return h + m/100 + s/10000

    match = re.match(
        r"^(\d+):(\d{1,2})$",
        text
    )

    if match:

        h = int(match.group(1))
        m = int(match.group(2))

        return h + m/100

    try:

        return float(text)

    except:

        return np.nan


# ==========================================================
# NUMERIC CHECK
# ==========================================================

def is_numeric(value):

    try:

        if pd.isna(value):
            return False

        float(value)

        return True

    except:

        return False


# ==========================================================
# EXTRACT PEAKS FROM ONE GCMS FILE
# ==========================================================

def extract_peaks(filepath):

    print(f"\nReading: {os.path.basename(filepath)}")

    raw = pd.read_excel(
        filepath,
        header=None
    )

    peaks = []

    current_mz = None

    for _, row in raw.iterrows():

        if len(row) < 5:
            continue

        first = str(row.iloc[0]).strip()

        ric = re.search(
            r"RIC\s*(?:=|:)?\s*(\d+)",
            first,
            re.IGNORECASE
        )

        if ric:

            current_mz = int(
                ric.group(1)
            )

            continue

        if current_mz is None:
            continue

        raw_rt = row.iloc[2]
        raw_area = row.iloc[3]
        raw_percent = row.iloc[4]

        if not is_numeric(raw_area):
            continue

        rt = parse_raw_rt(raw_rt)

        if pd.isna(rt):
            continue

        peaks.append({

            "m/z": current_mz,

            "Range": row.iloc[0],

            "Peak": row.iloc[1],

            "Raw RT": raw_rt,

            "RT": float(rt),

            "Area": float(raw_area),

            "% Area": float(raw_percent)
            if is_numeric(raw_percent)
            else 0

        })

    peak_df = pd.DataFrame(peaks)

    print(
        "Total Peaks:",
        len(peak_df)
    )

    return peak_df

# ==========================================================
# MATCH THE 22 VOCs
# ==========================================================

def extract_vocs(peak_df):

    output = []

    detected_count = 0

    for voc_name, reference_rt, target_mz, threshold in VOC_REFERENCE:

        matching_mz = peak_df[
            peak_df["m/z"] == target_mz
        ].copy()

        result = {

            "VOC": voc_name,

            "Reference RT": reference_rt,

            "m/z": target_mz,

            "Detected RT": 0,

            "Area": 0,

            "% Area": 0,

            "Status": "NOT DETECTED"

        }

        if matching_mz.empty:

            output.append(result)

            continue

        matching_mz["RT Difference"] = (

            matching_mz["RT"] - reference_rt

        ).abs()

        valid_peaks = matching_mz[

            matching_mz["RT Difference"] <= threshold

        ].copy()

        if valid_peaks.empty:

            output.append(result)

            continue

        best = valid_peaks.loc[

            valid_peaks["RT Difference"].idxmin()

        ]

        detected_count += 1

        result = {

            "VOC": voc_name,

            "Reference RT": reference_rt,

            "m/z": target_mz,

            "Detected RT": best["RT"],

            "Area": best["Area"],

            "% Area": best["% Area"],

            "Status": "DETECTED"

        }

        output.append(result)

    result_df = pd.DataFrame(output)

    return result_df, detected_count


# ==========================================================
# PROCESS ONE FILE
# ==========================================================

def process_file(filepath):

    peak_df = extract_peaks(filepath)

    result_df, detected_count = extract_vocs(peak_df)

    sample_name = os.path.splitext(

        os.path.basename(filepath)

    )[0]

    area_df = result_df[

        ["VOC", "Area"]

    ].copy()

    area_df.rename(

        columns={

            "Area": sample_name

        },

        inplace=True

    )

    print(

        f"Processed {sample_name}"

    )

    print(

        f"Detected within threshold: {detected_count}/22"

    )

    return area_df

# ==========================================================
# PROCESS ENTIRE FOLDER
# ==========================================================

def process_folder(input_folder, output_file):

    files_processed = 0

    area_tables = {}

    for filename in sorted(os.listdir(input_folder)):

        if not filename.lower().endswith((".xlsx", ".xls")):
            continue

        # Ignore previously generated files
        if "_VOC" in filename:
            continue

        if filename.startswith("~$"):
            continue

        input_path = os.path.join(
            input_folder,
            filename
        )

        area_df = process_file(input_path)

        sample_name = os.path.splitext(filename)[0]

        area_tables[sample_name] = area_df

        files_processed += 1

    print("\n==============================================")
    print("ALL GCMS FILES COMPLETED")
    print("Files processed:", files_processed)
    print("==============================================")

    print("\nCreating Combined Area sheet...")

    combined = None

    voc_order = [

        voc[0]

        for voc in VOC_REFERENCE

    ]

    for sample_name, df in area_tables.items():

        df["VOC"] = pd.Categorical(

            df["VOC"],

            categories=voc_order,

            ordered=True

        )

        df = df.sort_values("VOC")

        if combined is None:

            combined = df

        else:

            combined = combined.merge(

                df,

                on="VOC",

                how="outer"

            )

    combined["VOC"] = pd.Categorical(

        combined["VOC"],

        categories=voc_order,

        ordered=True

    )

    combined = combined.sort_values("VOC")

    # Fill only the numeric columns with 0
    combined.iloc[:, 1:] = combined.iloc[:, 1:].fillna(0)

    combined.to_excel(

        output_file,

        index=False

    )

    print("\n==============================================")
    print("Combined Area sheet saved.")
    print(output_file)
    print("==============================================")

    return output_file