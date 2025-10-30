import pandas as pd
import numpy as np
from collections import defaultdict
import json

# LOAD DATA
hhv1_path = r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\hhv1\hhv1_cleaned.json"
hhrv_path = r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\hhrv\hhrv_cleaned.json"
perv1_path = r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\perv1\perv1_cleaned.json"
perrv_path = r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\perrv\perrv_cleaned.json"

hhv1 = pd.read_json(hhv1_path)
hhrv = pd.read_json(hhrv_path)
perv1 = pd.read_json(perv1_path)
perrv = pd.read_json(perrv_path)

# FILTER TO VALID HOUSEHOLDS (for hhv1 and hhrv)
household_filter = (
    (hhv1["Survey Code"] == "household surveyed: original") &
    (hhv1["Response Code"].str.contains("co-operative and capable", case=False, na=False))
)
hhv1 = hhv1[household_filter]

household_filter_hhrv = (
    (hhrv["Survey Code"] == "household surveyed: original") &
    (hhrv["Response Code"].str.contains("co-operative and capable", case=False, na=False))
)
hhrv = hhrv[household_filter_hhrv]

# COMPUTE FINAL WEIGHTS
multiplier_col = "Sub-sample wise Multiplier"
nss_col = "Ns count for sector x stratum x substratum x sub-sample"
nsc_col = "Ns count for sector x stratum x substratum"
no_qtr_col = "Count of contributing State x Sector x Stratum x SubStratum in 4 Quarters"

# Adjusted weight calculation with proper pandas handling
for df in [hhv1, hhrv, perv1, perrv]:
    df['final_weight'] = np.where(df[nss_col] == df[nsc_col], 
                             (df[multiplier_col] / 100) / df[no_qtr_col], 
                             (df[multiplier_col] / 200 / df[no_qtr_col]))

def weighted_distribution(series, weights, top_n=5):
    mask = series.notna()
    series = series[mask]
    weights = weights[mask]
    value_weight = defaultdict(float)
    for val, w in zip(series, weights):
        value_weight[str(val)] += w
    sorted_items = sorted(value_weight.items(), key=lambda x: x[1], reverse=True)
    top_items = sorted_items[:top_n]
    top_keys = [x[0] for x in top_items]
    other_weight = sum(w for k, w in sorted_items[top_n:])
    dist_total = sum(value_weight.values())
    out = {k: float(v) / dist_total for k, v in top_items}
    if other_weight > 0:
        out['other'] = float(other_weight) / dist_total
    return out

def weighted_average(series, weights):
    mask = series.notna()
    return float(np.average(series[mask], weights=weights[mask])) if mask.any() else np.nan

def weighted_median(series, weights):
    mask = series.notna()
    sr, wt = series[mask], weights[mask]
    sorter = np.argsort(sr)
    sr, wt = sr.iloc[sorter], wt.iloc[sorter]
    cum_weights = np.cumsum(wt)
    cutoff = cum_weights.iloc[-1] / 2
    idx = np.searchsorted(cum_weights, cutoff)
    return float(sr.iloc[idx])

# AGGREGATION BY SECTOR AND STATE
def aggregate_household_weighted(df, sector = "urban"):
    result = {}
    # grouped = df[df["Sector"] == sector].groupby("State/Ut Code")
    grouped = df.groupby("State/Ut Code")
    for state, group in grouped:
        w = group['final_weight']
        result[state] = {
            # "total_households": float(w.sum()),
            # "population_estimate": float((group["Household Size"] * w).sum()),
            "avg_household_size": weighted_average(group["Household Size"], w),
            "household_type_distribution": weighted_distribution(group["Household Type"], w),
            "religion_distribution": weighted_distribution(group["Religion"], w),
            "social_group_distribution": weighted_distribution(group["Social Group"], w),
            "avg_monthly_expenditure": weighted_average(group["Household'S Usual Consumer Expenditure In A Month (Rs.)"], w),
            "median_monthly_expenditure": weighted_median(group["Household'S Usual Consumer Expenditure In A Month (Rs.)"], w),
            "expenditure_distribution": group["Household'S Usual Consumer Expenditure In A Month (Rs.)"].describe(percentiles=[.1, .25, .5, .75, .9]).to_dict(),
        }
    return result

status_mapping = {
            "worked in h.h. enterprise (self-employed): own account worker": "employed",
            "worked in h.h. enterprise (self-employed): employer": "employed",
            "worked as helper in h.h. enterprise (unpaid family worker)": "employed",
            "worked as regular salaried/wage employee": "employed",
            "worked as casual wage labour: in public works": "employed",
            "worked as casual wage labour: in other types of work": "employed",
            "did not work but was seeking and/or available for work": "unemployed",
            "attended educational institution": "not_in_labor_force",
            "attended domestic duties only": "not_in_labor_force",
            "attended domestic duties and was also engaged in free collection of goods (vegetables, roots, firewood, cattle feed, etc.), sewing, tailoring, weaving, etc. for household use": "not_in_labor_force",
            "rentiers, pensioners, remittance recipients, etc.": "not_in_labor_force",
            "not able to work due to disability": "not_in_labor_force",
            "others (including begging, prostitution, etc.)": "not_in_labor_force"
        }

with open(r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\industry_codes.json", "r", encoding="utf-8") as f:
    nic_2digit_mapping = json.load(f)

with open(r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\occupation_codes.json", "r", encoding="utf-8") as f:
    occupation_codes_mapping = json.load(f)

print(1)

def aggregate_person_weighted(df, sector = "urban"):
    # grouped = df[df["Sector"] == sector].groupby("State/Ut Code")
    grouped = df.groupby("State/Ut Code")
    result = defaultdict(dict)
    for state, group in grouped:
        w = group['final_weight']
        total_pop = w.sum()

        # occ_code = group["Occupation Code (NCO)"]
        occ_code = group["Occupation Code (NCO)"]
        ind_code = group["Industry Code (NIC)"]

        # Compute distributions with descriptive text
        occ_dist = weighted_distribution(occ_code, w)
        ind_dist = weighted_distribution(ind_code, w)

        # Convert distributions to codes
        def map_to_code(dist, mapping,check):
            if not dist:
                return {}

            code_dist = {}
            for desc, prop in dist.items():
                # Handle numbers or numeric strings
                try:
                    val = float(desc)
                    # Convert to integer if whole number, then string to extract first two digits
                    if val.is_integer():
                        val_str = str(int(val))
                    else:
                        val_str = str(int(val))  # safely truncate decimals
                    if check == 1:
                        desc_key = val_str[:2]  # take only first two characters (e.g., "10" from "101")
                    else:
                        desc_key = val_str[:3]
                except (ValueError, TypeError):
                    # Not numeric → use as is
                    desc_key = desc

                # Find code for description, else use numeric key
                code = mapping.get(desc_key, desc_key)
                # print(code)
                code_dist[code] = prop

            return code_dist


        # Map status sentences to categories
        status_cat = group["Status Code"].map(lambda x: status_mapping.get(x, "unknown"))
        employed_mask = status_cat == "employed"
        unemployed_mask = status_cat == "unemployed"
        labor_force_mask = employed_mask | unemployed_mask

        # Vocational training percentage (combine "yes" categories)
        vocational_training = group["Whether received any Vocational/Technical Training"]
        mask = vocational_training.notna()
        voc_training_series = vocational_training[mask].copy()
        voc_weights = w[mask]
        # Map all "yes" responses to "yes", others to "no"
        voc_training_series = voc_training_series.map(
            lambda x: "yes" if "received" in str(x).lower() or "yes" in str(x).lower() else "no"
        )
        voc_training_pct = weighted_distribution(voc_training_series, voc_weights)

        result[state].update({
            "gender_ratio": weighted_distribution(group["Gender"], w),
            "age_distribution": dict(zip(
                ["0-14", "15-29", "30-59", "60+"],
                [
                    weighted_average(group["Age"] < 15, w),
                    weighted_average((group["Age"] >= 15) & (group["Age"] < 30), w),
                    weighted_average((group["Age"] >= 30) & (group["Age"] < 60), w),
                    weighted_average(group["Age"] >= 60, w)
                ]
            )),
            "marital_status_distribution": weighted_distribution(group["Marital Status"], w),
            "education_distribution": weighted_distribution(group["General Educaion Level"], w),
            "technical_education_distribution": weighted_distribution(group["Technical Educaion Level"], w),
            "avg_years_formal_education": weighted_average(group["No. of years in Formal Education"], w),
            "vocational_training_percentage": voc_training_pct,
            # "vocational_training_percentage": weighted_distribution(group["Whether received any Vocational/Technical Training"], w),
            "occupation_distribution": map_to_code(occ_dist, occupation_codes_mapping,2),
            "industry_distribution": map_to_code(ind_dist, nic_2digit_mapping,1),"avg_regular_wage_earning": weighted_average(group["Earnings For Regular Salaried/Wage Activity"], w),
            "median_regular_wage_earning": weighted_median(group["Earnings For Regular Salaried/Wage Activity"], w),
            "avg_self_employed_earning": weighted_average(group["Earnings For Self Employed"], w),
            "median_self_employed_earning": weighted_median(group["Earnings For Self Employed"], w),
            # "wpr": float(employed_weight / total_pop) if total_pop > 0 else 0.0,
            # "lfpr": float(labor_force_weight / total_pop) if total_pop > 0 else 0.0,
            # "ur": float(w[unemployed_mask].sum() / labor_force_weight) if labor_force_weight > 0 else 0.0,
            # "total_population": float(total_pop)
        })
        # print(result)
    return result


# Aggregate for both sectors from v1 files
hh_data = aggregate_household_weighted(hhv1)
# hh_rural = aggregate_household_weighted(hhv1, "rural")
per_data = aggregate_person_weighted(perv1)
# per_rural = aggregate_person_weighted(perv1, "rural")

# Combine results by state
final_state_data = {}
for state in set(hh_data.keys()).union(per_data.keys()):
    final_state_data[state] = {}
    final_state_data[state] = {**hh_data.get(state, {}), **per_data.get(state, {})}
    # final_state_data[state]["rural"] = {**hh_rural.get(state, {}), **per_rural.get(state, {})}


def pytype(o):
    if isinstance(o, dict):
        return {k: pytype(v) for k, v in o.items()}
    elif isinstance(o, list):
        return [pytype(x) for x in o]
    elif isinstance(o, np.integer):
        return int(o)
    elif isinstance(o, np.floating):
        return float(o)
    else:
        return o

import json
with open("statewise_plfs_combined.json", "w") as f:
    json.dump(pytype(final_state_data), f, indent=2)

print("Done! Statewise PLFS data (weighted, filtered) written to statewise_plfs_weighted.json")