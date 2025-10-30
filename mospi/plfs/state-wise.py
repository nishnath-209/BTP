import pandas as pd
import numpy as np
from collections import Counter, defaultdict

hhv1_path = r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\hhv1\hhv1_cleaned.json"
hhrv_path = r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\hhrv\hhrv_cleaned.json"
perv1_path = r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\perv1\perv1_cleaned.json"
perrv_path = r"C:\Users\nishn\OneDrive\Desktop\BTP\Data BTP\Data\mospi\plfs\perrv\perrv_cleaned.json"

def safe_read_json(path):
    try:
        return pd.read_json(path, lines=True)
    except ValueError:
        print(f"⚠️ Retrying {path} without 'lines=True'")
        return pd.read_json(path)

hhv1 = pd.read_json(hhv1_path)
hhrv = pd.read_json(hhrv_path)
perv1 = pd.read_json(perv1_path)
perrv = pd.read_json(perrv_path)


def get_mode(series):
    return series.mode().iloc[0] if not series.mode().empty else np.nan

def get_distribution(series):
    value_counts = series.value_counts(dropna=True)
    return {str(k): float(v) / len(series) for k, v in value_counts.items()}


def aggregate_household(hh_df):
    grouped = hh_df.groupby('State/Ut Code')
    result = {}
    for state, group in grouped:
        result[state] = {
            "total_households": group.shape[0],
            "avg_household_size": group["Household Size"].mean(),
            "household_type_distribution": get_distribution(group["Household Type"]),
            "religion_distribution": get_distribution(group["Religion"]),
            "social_group_distribution": get_distribution(group["Social Group"]),
            "avg_monthly_expenditure": group["Household'S Usual Consumer Expenditure In A Month (Rs.)"].mean(),
            "median_monthly_expenditure": group["Household'S Usual Consumer Expenditure In A Month (Rs.)"].median(),
            "expenditure_distribution": group["Household'S Usual Consumer Expenditure In A Month (Rs.)"].describe(percentiles=[.1, .25, .5, .75, .9]).to_dict()
        }
    return result


def aggregate_person(pv_df):
    grouped = pv_df.groupby('State/Ut Code')
    result = defaultdict(dict)
    for state, group in grouped:
        n = group.shape[0]
        result[state].update({
            "total_population": n,
            "gender_ratio": get_distribution(group["Gender"]),
            "age_distribution": dict(zip(
                ["0-14", "15-29", "30-59", "60+"],
                [
                    (group["Age"] < 15).mean(),
                    ((group["Age"] >= 15) & (group["Age"] < 30)).mean(),
                    ((group["Age"] >= 30) & (group["Age"] < 60)).mean(),
                    (group["Age"] >= 60).mean()
                ]
            )),
            "marital_status_distribution": get_distribution(group["Marital Status"]),
            "education_distribution": get_distribution(group["General Educaion Level"]),
            "technical_education_distribution": get_distribution(group["Marital Status"]),
            "avg_years_formal_education": group["No. of years in Formal Education"].mean(),
            "vocational_training_percentage": (group["Whether received any Vocational/Technical Training"] == 1).mean(),
            "principal_activity_status_distribution": get_distribution(group["Status Code"]),
            "occupation_distribution": get_distribution(group["Occupation Code (NCO)"]),
            "industry_distribution": get_distribution(group["Industry Code (NIC)"]),
            "avg_regular_wage_earning": group["Earnings For Regular Salaried/Wage Activity"].mean(),
            "median_regular_wage_earning": group["Earnings For Regular Salaried/Wage Activity"].median(),
            "avg_self_employed_earning": group["Earnings For Self Employed"].mean(),
            "median_self_employed_earning": group["Earnings For Self Employed"].median()
            # Add weekly wage if available: "avg_weekly_wage": group["b6q9_3pt1_perv1"].mean(), etc.
        })
    return result

# Aggregate household and person
household_state = aggregate_household(hhv1)
person_state = aggregate_person(perv1)

# Merge for final output
final_state_data = {}
for state in household_state:
    final_state_data[state] = {**household_state[state], **person_state.get(state, {})}

# Save or use `final_state_data` as needed (e.g., json.dump)
import json
with open("statewise_plfs.json", "w") as f:
    json.dump(final_state_data, f, indent=2)
