import pandas as pd
import numpy as np
from collections import defaultdict

# LOAD DATA
hhv1_path = r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\hhv1\hhv1_cleaned.json"
hhrv_path = r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\hhrv\hhrv_cleaned.json"
perv1_path = r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\perv1\perv1_cleaned.json"
perrv_path = r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\perrv\perrv_cleaned.json"


hhv1 = pd.read_json(hhv1_path)
perv1 = pd.read_json(perv1_path)

# FILTER TO VALID HOUSEHOLDS (do this before everything else)
household_filter = (
    (hhv1["Survey Code"] == "household surveyed: original") &
    (hhv1["Response Code"].str.contains("co-operative and capable", case=False, na=False))
)
hhv1 = hhv1[household_filter]

# Use correct weight field
hhv1['weight'] = hhv1['Sub-sample wise Multiplier']
perv1['weight'] = perv1['Sub-sample wise Multiplier'] if 'Sub-sample wise Multiplier' in perv1.columns else 1.0

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
    # nan-safe weighted median
    mask = series.notna()
    sr, wt = series[mask], weights[mask]
    sorter = np.argsort(sr)
    sr, wt = sr.iloc[sorter], wt.iloc[sorter]
    cum_weights = np.cumsum(wt)
    cutoff = cum_weights.iloc[-1] / 2
    idx = np.searchsorted(cum_weights, cutoff)
    return float(sr.iloc[idx])

# THE AGGREGATION
def aggregate_household_weighted(df):
    result = {}
    grouped = df.groupby('State/Ut Code')
    for state, group in grouped:
        w = group['weight']
        result[state] = {
            "total_households": float(w.sum()),
            "population_estimate": float((group["Household Size"] * w).sum()),
            "avg_household_size": weighted_average(group["Household Size"], w),
            "household_type_distribution": weighted_distribution(group["Household Type"], w),
            "religion_distribution": weighted_distribution(group["Religion"], w),
            "social_group_distribution": weighted_distribution(group["Social Group"], w),
            "avg_monthly_expenditure": weighted_average(group["Household'S Usual Consumer Expenditure In A Month (Rs.)"], w),
            "median_monthly_expenditure": weighted_median(group["Household'S Usual Consumer Expenditure In A Month (Rs.)"], w),
            "expenditure_distribution": group["Household'S Usual Consumer Expenditure In A Month (Rs.)"].describe(percentiles=[.1, .25, .5, .75, .9]).to_dict(),
            # ... add more fields as needed ...
        }
    return result

def aggregate_person_weighted(df):
    grouped = df.groupby('State/Ut Code')
    result = defaultdict(dict)
    for state, group in grouped:
        w = group['weight']
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
            "vocational_training_percentage": weighted_average(group["Whether received any Vocational/Technical Training"] == 1, w),
            "principal_activity_status_distribution": weighted_distribution(group["Status Code"], w),
            "occupation_distribution": weighted_distribution(group["Occupation Code (NCO)"], w),
            "industry_distribution": weighted_distribution(group["Industry Code (NIC)"], w),
            "avg_regular_wage_earning": weighted_average(group["Earnings For Regular Salaried/Wage Activity"], w),
            "median_regular_wage_earning": weighted_median(group["Earnings For Regular Salaried/Wage Activity"], w),
            "avg_self_employed_earning": weighted_average(group["Earnings For Self Employed"], w),
            "median_self_employed_earning": weighted_median(group["Earnings For Self Employed"], w),
            "total_population": float(w.sum())
        })
    return result

household_state = aggregate_household_weighted(hhv1)
person_state = aggregate_person_weighted(perv1)

final_state_data = {}
for state in household_state:
    final_state_data[state] = {**household_state[state], **person_state.get(state, {})}

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
with open("statewise_plfs_weighted.json", "w") as f:
    json.dump(pytype(final_state_data), f, indent=2)

print("Done! Statewise PLFS data (weighted, filtered) written to statewise_plfs_weighted.json")
