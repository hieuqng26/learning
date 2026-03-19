import pandas as pd
import numpy as np
import os, sys
import json
import re
from datetime import datetime
from pathlib import Path

project_root = os.path.abspath("../../..")
sys.path.append(project_root)

from mst.model.SF_CG.SF_CG_config import *
from utils.compare_file import compare_csv, compare_excel
from utils.log_file import Timestamplog

file_keyword = LOG_DIR / "SF CG"
sys.stdout = Timestamplog(file_keyword)

# ===== Config =====
with open('./mst/model/SF_CG/cg_config.json', 'r') as f:
    config = json.load(f)

scenario_name = config.get("scenario")
TIMEPOINT = config.get("t1_timepoint")

apply_score_distribution_not_max_prob_score = True

base_path = PROJECT_DIR / "6. Revised model" / "3. SF"
INPUT_DIR = base_path / "1) Input" / "5) CG"
OUTPUT_DIR = base_path / "2) Output" / "5) CG"
QUAL_FACTOR_INPUT_DIR = INPUT_DIR / "1) Qual Factor"
CHARTERER_CG_INPUT_DIR = Path(USER_SPECIFIC_PATH) / "84. Deloitte Modelling" / "82. Spec_Lending" / "6. Revised model" / "3. SF" / "Charter_1303"
RISK_FILE_DIR = INPUT_DIR / "3) Risk Data"
STATIC_INPUT_DIR = INPUT_DIR / "6) Static Data"
MISC_INPUT_DIR = INPUT_DIR / "7) Others"
MEV_INPUT_DIR = base_path / "7) Other_inputs"

DO_OUTPUT_DEBUG_FILE = False
if DO_OUTPUT_DEBUG_FILE:
    os.makedirs(OUTPUT_DIR / "debug", exist_ok=True)

outputIndividualFile = False
beta_file = "Stress testing input(optim_all_60_affine_skip).xlsx"
AWE_COUNTRIES = list(CGP_FX_WEIGHTED_AVE.keys())
os.makedirs(OUTPUT_DIR, exist_ok=True)


def output_summary_table(df_input, type_name, file_postfix, impact_indicator_name, category_name, outputIndividualFile):
    df = df_input.copy()
    n_deals = len(df['main_profile_leid'].unique())
    df = df.rename(columns={impact_indicator_name: 'Impact_Indicator_name',
                             category_name: 'Category_name'})
    df_impact = df.groupby(["Impact_Indicator_name", "Category_name"]).agg({"main_profile_leid": "count"})
    df_impact['main_profile_leid'] = df_impact['main_profile_leid'] / n_deals

    df_impact_key = df_impact.copy().reset_index()
    df_key_cols = list(df_impact_key.columns.values)
    df_impact_key["Config"] = scenario_name + TIMEPOINT
    df_impact_key["Type"] = type_name
    df_impact_key["Key"] = (df_impact_key["Config"]
                            + df_impact_key["Impact_Indicator_name"]
                            + df_impact_key["Category_name"])
    df_impact_key = df_impact_key[["Key", "Type"] + df_key_cols]

    df_impact = df_impact.pivot_table(index=["Impact_Indicator_name"], columns="Category_name", values=["main_profile_leid"])
    cols = df_impact.columns
    new_cols = [first if second == "" else second for first, second in cols.values]
    df_impact.columns = new_cols
    col_order = [">= 3.5 notches", "between 2-3 notches", "<=1.5 notches", "Flat", "Upgrade"]
    ordered_col = ["Impact_Indicator_name"] + [c for c in col_order if c in new_cols]
    df_impact = df_impact[ordered_col]

    if outputIndividualFile:
        out_path3 = OUTPUT_DIR / f"{scenario_name}_{TIMEPOINT}_{file_postfix}.xlsx"
        with pd.ExcelWriter(out_path3, engine="xlsxwriter") as writer:
            df_impact_key.to_excel(writer, sheet_name="KeyTable", index=False)
            df_impact.to_excel(writer, sheet_name="PivotTable", index=False)
        if COMPARE_OUTPUT:
            compare_excel(out_path3)
    return df_impact_key


# ── MEV transformations ────────────────────────────────────────────────────

scenario_file = SCENARIOS[scenario_name]
beta = pd.read_excel(QUAL_FACTOR_INPUT_DIR / beta_file, sheet_name="Sheet1")
abc = pd.read_csv(scenario_file)
MEV_LIST = abc['concept'].unique()


def identify_mev(text, mev_list):
    text = str(text)
    hits = [m for m in mev_list if m in text]
    return hits[0] if hits else None


def parse_country(mev_str):
    s = str(mev_str)
    m = re.search(r'_(\w{2})_', s)
    if m:
        return m.group(1)
    return s[4:6] if len(s) >= 6 else None


def parse_ma(text):
    s = str(text)
    m = re.search(r'(\d+)\s*QMA', s, flags=re.I)
    if not m:
        m = re.search(r'QMA\s*(\d+)', s, flags=re.I)
    return int(m.group(1)) if m else None


def identify_lag(transformation_list):
    transformation = [t for t in transformation_list if 'lag' in t]
    lag_transform = ','.join(transformation)
    if lag_transform:
        return int(lag_transform[3])
    return None


def parse_yoy(text):
    s = str(text)
    if re.search(r'yoy', s, flags=re.I):
        m = re.search(r'yoy[_\s-]?(\d+)', s, flags=re.I)
        return int(m.group(1)) if m else 4
    return None


def apply_transformations(scn_df, concept, country, tp, ma_quarters=None, yoy=None, lag=None):
    row = scn_df[(scn_df['concept'] == concept) & (scn_df['country'] == country)]
    if row.empty:
        return np.nan
    long_df = pd.melt(row, id_vars=['type', 'concept', 'country'],
                      var_name='variable', value_name='value').copy()
    long_df['t'] = pd.to_numeric(long_df['variable'].str.extract(r'(\d+)', expand=False), errors='coerce')
    long_df['t'] = np.where(long_df['variable'].str.contains('-minus'), -long_df['t'], long_df['t'])
    long_df = long_df.sort_values('t').reset_index(drop=True)

    out = 'value'
    if ma_quarters is not None and not pd.isna(ma_quarters):
        w = int(ma_quarters)
        long_df['moving_average'] = long_df[out].rolling(w, min_periods=w).mean()
        out = 'moving_average'
    if yoy is not None and not pd.isna(yoy):
        k = int(yoy)
        if concept in ["Unemployment rate", "Investment Grade Emerging Markets Bond Index",
                       "Eurozone Bond Index", "SubInvestment Grade Emerging Markets Bond Index",
                       "Monetary policy or key interest rate"]:
            long_df['yoy'] = (long_df[out] - long_df[out].shift(k)) / 100
        else:
            long_df['yoy'] = (long_df[out] - long_df[out].shift(k)) / long_df[out].shift(k)
        out = 'yoy'
    if lag is not None and not pd.isna(lag):
        l = int(lag)
        long_df['lag'] = long_df[out].shift(l)
        out = 'lag'

    val = long_df.loc[long_df['variable'] == tp, out]
    return val.iloc[0] if not val.empty else np.nan


beta['Mev_Country'] = beta['Mev'].apply(parse_country)
beta['Mev_Transformation'] = beta['Mev'].astype(str).str.replace('lag_', 'lag', regex=False)
beta['Mev_Concept'] = beta['Mev_Transformation'].apply(lambda x: identify_mev(x, MEV_LIST))
beta['moving_average'] = beta['Mev_Transformation'].apply(parse_ma)
beta['transformation_list'] = beta['Mev_Transformation'].str.replace('lag_', 'lag').str.split('_')
beta['lag'] = beta['transformation_list'].apply(identify_lag)
beta['yoy'] = beta['Mev_Transformation'].apply(parse_yoy)

beta[f'mev_value_{TIMEPOINT}'] = beta.apply(
    lambda r: apply_transformations(
        abc, r['Mev_Concept'], r['Mev_Country'], TIMEPOINT,
        ma_quarters=r['moving_average'], yoy=r['yoy'], lag=r['lag']
    ), axis=1
)

if 'Beta' in beta.columns:
    beta['contribution'] = beta[f'mev_value_{TIMEPOINT}'] * beta['Beta']

if DO_OUTPUT_DEBUG_FILE:
    out_path = OUTPUT_DIR / "debug" / f"mev_transformed_{TIMEPOINT}.csv"
    beta.to_csv(out_path, index=False)


# ── Real GDP weights ───────────────────────────────────────────────────────

mev_df = pd.read_csv(MEV_hist_PATH)
mev_df_date_selected = mev_df[mev_df["Date"] == DATE_REF_WEIGHTED_AVE]
mev_dict = mev_df_date_selected["Date"].to_dict("records")[0]
fx_country = [1 if c == "US" else (mev_dict[c + "_FX rate"]) for c in AWE_COUNTRIES]
real_gdp_lcy = [mev_dict[c + "_Real GDP"] for c in AWE_COUNTRIES]
real_gdp_usd = [real_gdp_lcy[i] * fx_country[i] for i in range(len(real_gdp_lcy))]
real_gdp_usd_sum = sum(real_gdp_usd)
raw_weights = {AWE_COUNTRIES[i]: real_gdp_usd[i] / real_gdp_usd_sum for i in range(len(real_gdp_usd))}


# ── GDP-weighted average MEV ───────────────────────────────────────────────

beta_for_ave = pd.read_excel(QUAL_FACTOR_INPUT_DIR / beta_file, sheet_name="Sheet1")
AWE_MEVS = set(beta_for_ave['Mev'].str.match('Ave_')['Mev_Concept'].values)


def _long_for(concept, country):
    row = abc[(abc['concept'] == concept) & (abc['country'] == country)]
    if row.empty:
        return None
    df = pd.melt(row, id_vars=['type', 'concept', 'country'],
                 var_name='variable', value_name='value').copy()
    df['t'] = pd.to_numeric(df['variable'].str.extract(r'(\d+)', expand=False), errors='coerce')
    df['t'] = np.where(df['variable'].str.contains('-minus'), -df['t'], df['t'])
    return df.sort_values('t').reset_index(drop=True)


def apply_transformations_single(concept, country, tp, ma_quarters=None, yoy=None, lag=None):
    df = _long_for(concept, country)
    if df is None:
        return np.nan
    out = df['value']
    if ma_quarters is not None and pd.notna(ma_quarters):
        out = out.rolling(int(ma_quarters), min_periods=int(ma_quarters)).mean()
    if yoy is not None and pd.notna(yoy):
        if concept in ["Investment Grade Emerging Markets Bond Index", "Eurozone Bond Index",
                       "Monetary policy or key interest rate"]:
            out = (out - out.shift(int(yoy))) / 100
        else:
            out = (out - out.shift(int(yoy))) / out.shift(int(yoy))
    if lag is not None and pd.notna(lag):
        out = out.shift(int(lag))
    val = df.loc[df['variable'] == tp, out.name if hasattr(out, 'name') else 'value']
    return val.iloc[0] if not val.empty else np.nan


def apply_transformations_weighted(concept, countries, weights, tp, ma=None, yoy=None, lag=None):
    available, wts = [], []
    for c in countries:
        if (abc['concept'].eq(concept) & abc['country'].eq(c)).any():
            available.append(c)
            wts.append(weights.get(c, 0.0))
    if not available or sum(wts) == 0:
        return np.nan
    wts = np.array(wts, dtype=float) / sum(wts)
    vals = []
    for c, wt in zip(available, wts):
        v = apply_transformations_single(
            concept, c, tp,
            ma_quarters=ma if (ma is not None and pd.notna(ma)) else None,
            yoy=yoy if (yoy is not None and pd.notna(yoy)) else None,
            lag=lag if (lag is not None and pd.notna(lag)) else None,
        )
        vals.append(wt * v if pd.notna(v) else np.nan)
    vals = [x for x in vals if pd.notna(x)]
    return sum(vals) if vals else np.nan


beta_for_ave['Mev_Country'] = beta_for_ave['Mev'].apply(parse_country)
beta_for_ave['Mev_Transformation'] = beta_for_ave['Mev'].astype(str).str.replace('lag_', 'lag', regex=False)
beta_for_ave['Mev_Concept'] = beta_for_ave['Mev_Transformation'].apply(lambda x: next((m for m in AWE_MEVS if m in x), None))
beta_for_ave['moving_average'] = beta_for_ave['Mev_Transformation'].apply(parse_ma)
beta_for_ave['transformation_list'] = beta_for_ave['Mev_Transformation'].str.replace('lag_', 'lag').str.split('_')
beta_for_ave['lag'] = beta_for_ave['transformation_list'].apply(identify_lag)
beta_for_ave['yoy'] = beta_for_ave['Mev_Transformation'].apply(parse_yoy)

beta_avg = beta_for_ave[beta_for_ave['Mev_Concept'].isin(AWE_MEVS)].copy()
beta_avg[f'mev_value_{TIMEPOINT}'] = beta_avg.apply(
    lambda r: apply_transformations_weighted(
        r['Mev_Concept'], AWE_COUNTRIES, raw_weights, TIMEPOINT,
        ma=r.get('moving_average'), yoy=r.get('yoy'), lag=r.get('lag')
    ), axis=1
)

if DO_OUTPUT_DEBUG_FILE:
    out_path = OUTPUT_DIR / "debug" / f"mev_average_only_{TIMEPOINT}.csv"
    beta_avg.to_csv(out_path, index=False)


# ── Merge transformed MEV with GDP-weighted average ────────────────────────

def ensure_mev_col(df):
    for c in df.columns:
        if c.strip().lower() == "mev":
            if c != "Mev":
                df.rename(columns={c: "Mev"}, inplace=True)
            return
    raise KeyError("Couldn't find 'Mev' column.")


def pick_value_col(df):
    for cand in [f"mev_value_{TIMEPOINT}", "mev_value", f"value_{TIMEPOINT}", "value"]:
        if cand in df.columns:
            return cand
    raise KeyError("Couldn't find a MEV value column.")


df_full = beta.copy()
df_full["transformation_list"] = df_full["transformation_list"].astype(str)
df_avg = beta_avg.copy()
df_avg["transformation_list"] = df_avg["transformation_list"].astype(str)

ensure_mev_col(df_full)
ensure_mev_col(df_avg)

value_full = pick_value_col(df_full)
value_avg = pick_value_col(df_avg)

avg_lookup = df_avg[["Mev", value_avg]].copy().rename(columns={value_avg: "_avg_value"})
merged = df_full.merge(avg_lookup, on="Mev", how="left")
mask = merged[value_full].isna() & merged["_avg_value"].notna()
merged.loc[mask, value_full] = merged.loc[mask, "_avg_value"]
merged.drop(columns=["_avg_value"], inplace=True)
transformed_MEV = merged.drop_duplicates()

if DO_OUTPUT_DEBUG_FILE:
    out_path = OUTPUT_DIR / "debug" / f"mev_transformed_with_avg_{TIMEPOINT}.csv"
    transformed_MEV.to_csv(out_path, index=False)


# ── Load threshold & score data ────────────────────────────────────────────

def clean_cols(df):
    return df.rename(columns=lambda c: c.strip().lower().replace(' ', '_').replace('.', ''))


thr = clean_cols(pd.read_excel(QUAL_FACTOR_INPUT_DIR / beta_file, sheet_name="Sheet2"))
thr = thr.rename(columns={
    'question_no': 'question',
    'ordinal_responses': 'ordinal_response',
    'risk_type': 'risk_type'
})
thr = thr[['question', 'responses', 'ordinal_response', 'threshold']]
thr['question'] = thr['question'].astype(str)
thr['responses'] = thr['responses'].astype(str)

score = clean_cols(pd.read_csv(PROJECT_DIR / "3. SF" / "2) Input" / "2) CG" / "sf_score_data.csv"))
score['date_of_approval_void_decline'] = pd.to_datetime(
    score['date_of_approval_void_decline'], errors='coerce')
score['date_of_approval_void_decline'] = score['date_of_approval_void_decline'].dt.strftime('%d-%m-%Y')
score = score.rename(columns={"unnamed:_0": "a"})

risk_mi = clean_cols(pd.read_csv(INPUT_DIR / "SF_DEC_2024_list.csv"))

score['non_fin_res_id'] = score['non_fin_res_id'].mask(
    (score['non_fin_ques_no'].isin([11, 15, 16, 17])) & (score['non_fin_res_id'] == 'C'), 'D')

latest_risk_file = RISK_FILE_DIR / "sf_risk.csv"
df_risk = pd.read_csv(latest_risk_file)
latest_cohortflag = df_risk['cohortflag'].max()
df_risk_latest = df_risk[df_risk['cohortflag'] == latest_cohortflag]

score_latst = score[score['main_profile_leid'].isin(df_risk_latest['leid'])]
score_latst.loc[score_latst['date_of_approval_void_decline'] == 'None', 'date_of_approval_void_decline'] = None
score_latst['date_of_approval_void_decline'] = score_latst['date_of_approval_void_decline'].apply(
    lambda x: datetime.strptime(x, '%d-%m-%Y') if x else None)

latst_date_per_leid = score_latst.groupby(['main_profile_leid']).agg({'date_of_approval_void_decline': 'max'})
score_latst = score_latst.merge(latst_date_per_leid,
                                on=['main_profile_leid', 'date_of_approval_void_decline'],
                                how='inner')

if 'non_fin_ques_no' in score_latst.columns and 'non_fin_res_id' in score_latst.columns:
    score_latst = score_latst.rename(columns={'non_fin_ques_no': 'q_join', 'non_fin_res_id': 'r_join'})
else:
    raise KeyError(f"Score data needs columns non_fin_ques_no/non_fin_res_id. Got: {score_latst.columns.tolist()}")

score_latst['q_join'] = score_latst['q_join'].astype(str)
score_latst['r_join'] = score_latst['r_join'].astype(str)

out = score_latst.merge(thr, how='left', left_on=['q_join', 'r_join'], right_on=['question', 'responses'])
out = out.drop(columns=['question', 'responses'])

final_cols = ['scorecard_seq_id', 'q_join', 'r_join', 'ordinal_response', 'threshold']

if DO_OUTPUT_DEBUG_FILE:
    out.to_csv(OUTPUT_DIR / "debug" / "score_with_thresholds.csv", index=False)


# ── Remove scorecard IDs with CG rating 13 or 14 ──────────────────────────

risk_mi['main_profile_leid'] = risk_mi['main_profile_leid'].astype(str)
out['main_profile_leid'] = out['main_profile_leid'].astype(str)

out_post_exclusion = (
    out
    .merge(risk_mi[['main_profile_leid', 'riskmi_cg']], on='main_profile_leid', how='left')
    .loc[lambda xi: ~xi['riskmi_cg'].isin(['13', '14'])]
)

out_post_exclusion.columns = out_post_exclusion.columns.str.strip().str.lower()
out_post_exclusion['r_join'] = out_post_exclusion['r_join'].astype(str).str.upper()

severity = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5}
out_post_exclusion['sev'] = out_post_exclusion['r_join'].map(severity)

out_post_exclusion_diff = (
    out_post_exclusion.groupby(['scorecard_seq_id', 'q_join'])['r_join']
    .transform('nunique') > 1
)
best_sev = (
    out_post_exclusion.groupby(['scorecard_seq_id', 'q_join'])['sev']
    .transform('min')
)
out_data = (
    out_post_exclusion
    .loc[(out_post_exclusion_diff & (out_post_exclusion['sev'] == best_sev))]
    .drop(columns=['sev'])
)


# ── Merge model weights ────────────────────────────────────────────────────

out_with_thr = out_data.copy()
model_weights_df = pd.read_csv(STATIC_INPUT_DIR / "sf_model_weights.csv")
out_with_thr["q_join"] = out_with_thr["q_join"].astype(str)
model_weights_df["non_fin_ques_no"] = model_weights_df["non_fin_ques_no"].astype(str)

out_with_thr_weights = out_with_thr.merge(
    model_weights_df, left_on="q_join", right_on="non_fin_ques_no", how="left")

loan_flag_data = pd.read_csv(MISC_INPUT_DIR / "sf_pd_data.csv")
loan_flag_data = loan_flag_data[["scorecard_seq_id", "loan_purpose"]].copy()
out_with_thr_weights["scorecard_seq_id"] = out_with_thr_weights["scorecard_seq_id"].astype(str)
loan_flag_data["scorecard_seq_id"] = loan_flag_data["scorecard_seq_id"].astype(str)
out_with_thr_weights = out_with_thr_weights.merge(loan_flag_data, on="scorecard_seq_id", how="left")

out_with_thr_weights_12 = out_with_thr_weights[out_with_thr_weights["q_join"] == "12"]
out_with_thr_weights_others = out_with_thr_weights[out_with_thr_weights["q_join"] != "12"]

out_with_thr_weights_12 = out_with_thr_weights_12.drop_duplicates(subset="scorecard_seq_id", keep="first")

out_with_thr_weights_12["qual_res_weight1"] = np.where(
    out_with_thr_weights_12["loan_purpose"] == "Post-Delivery Only",
    out_with_thr_weights_12["Post-Delivery"],
    out_with_thr_weights_12["PrexPost-Delivery"])

out_with_thr_weights_12["qual_res_weight2"] = np.where(
    (out_with_thr_weights_12["loan_purpose"] == "Post-Delivery Only")
    & (out_with_thr_weights_12["r_join"] == "C"),
    out_with_thr_weights_12["Post-Delivery_if_12_No"],
    np.where(
        (out_with_thr_weights_12["loan_purpose"] == "PrexPost-Delivery")
        & (out_with_thr_weights_12["r_join"] == "C"),
        out_with_thr_weights_12["PrexPost-Delivery_if_12_No"],
        out_with_thr_weights_12["qual_res_weight1"]))

out_with_thr_weights_12 = out_with_thr_weights_12.drop(columns=["qual_res_weight1"])
out_with_thr_weights_12["12_C_Indicator"] = np.where(out_with_thr_weights_12["r_join"] == "C", 1, 0)

out_with_thr_weights_others = out_with_thr_weights_others.merge(
    out_with_thr_weights_12[["scorecard_seq_id", "12_C_Indicator"]],
    on="scorecard_seq_id", how="left")

out_with_thr_weights_others["qual_res_weight1"] = np.where(
    out_with_thr_weights_others["loan_purpose"] == "Post-Delivery Only",
    out_with_thr_weights_others["Post-Delivery"],
    out_with_thr_weights_others["PrexPost-Delivery"])

out_with_thr_weights_others["qual_res_weight2"] = np.where(
    (out_with_thr_weights_others["loan_purpose"] == "Post-Delivery Only")
    & (out_with_thr_weights_others["12_C_Indicator"] == 1),
    out_with_thr_weights_others["Post-Delivery_if_12_No"],
    np.where(
        (out_with_thr_weights_others["loan_purpose"] == "PrexPost-Delivery")
        & (out_with_thr_weights_others["12_C_Indicator"] == 1),
        out_with_thr_weights_others["PrexPost-Delivery_if_12_No"],
        out_with_thr_weights_others["qual_res_weight1"]))

out_with_thr_weights_12.columns = out_with_thr_weights_12.columns.str.strip()
out_with_thr_weights_others.columns = out_with_thr_weights_others.columns.str.strip()
out_with_thr_weights_others = out_with_thr_weights_others.drop(columns=['12_C_Indicator'], errors='ignore')
out_with_thr_weights_12 = out_with_thr_weights_12.reindex(columns=out_with_thr_weights_others.columns)
out_with_thr_weights = pd.concat([out_with_thr_weights_others, out_with_thr_weights_12], ignore_index=True)


# ── Unstressed qual score ──────────────────────────────────────────────────

out_with_thr_weight = out_with_thr_weights.copy()

out_with_thr_weight['qual_res_weight2'] = (
    out_with_thr_weight['qual_res_weight2']
    .astype(str)
    .str.extract(r'([+-]?\d*\.?\d+)')[0]
    .astype(float)
    .div(100)
    .fillna(0.0)
)
out_with_thr_weight['score'] = pd.to_numeric(out_with_thr_weight['score'], errors='coerce').fillna(0.0)
out_with_thr_weight['weighted_unstressed_score'] = (
    out_with_thr_weight['qual_res_weight2'] * out_with_thr_weight['score'])

_nonzero = out_with_thr_weight[out_with_thr_weight['weighted_unstressed_score'] != 0]
unstressed_qual_score = (
    _nonzero.groupby('scorecard_seq_id', as_index=False)['weighted_unstressed_score'].sum())
unstressed_qual_score.rename(columns={'weighted_unstressed_score': 'unstressed_qual_score'}, inplace=True)
unstressed_qual_score['unstressed_qual_score'] = unstressed_qual_score['unstressed_qual_score'].round(5)

out_with_thr_weight = pd.merge(out_with_thr_weight, unstressed_qual_score, on='scorecard_seq_id', how='left')

if DO_OUTPUT_DEBUG_FILE:
    out_with_thr_weight.to_csv(
        OUTPUT_DIR / "debug" / "score_with_thresholds_weight_unstressed_qual_score.csv", index=False)


# ── Merge MEV beta ─────────────────────────────────────────────────────────

st = out_with_thr_weight
mev = transformed_MEV
mev['Question No.'] = mev['Mev'].astype(str)

out = st.merge(
    mev[['Question No.', 'Mev', f'mev_value_{TIMEPOINT}', 'Beta']],
    left_on='q_join', right_on='Question No.', how='left'
).drop(columns=['Question No.'], errors='ignore')

if DO_OUTPUT_DEBUG_FILE:
    output_file_path = OUTPUT_DIR / "debug" / f"score_thresh_mev_beta_{TIMEPOINT}.csv"
    out.to_csv(output_file_path, index=False)


# ── Compute latent_y ───────────────────────────────────────────────────────

df = out.copy()
is_prev = df['Mev'].astype(str).str.lower().eq('previous_rating')
x = np.where(is_prev, df['ordinal_response'], df[f'mev_value_{TIMEPOINT}'])
df['latent_y'] = df['Beta'] * x
latent_y_df = df.copy()

if DO_OUTPUT_DEBUG_FILE:
    df.to_csv(OUTPUT_DIR / "debug" / "latent_y.csv", index=False)


# ── Ordinal response threshold pivot ──────────────────────────────────────

thresholds_df = pd.read_excel(QUAL_FACTOR_INPUT_DIR / beta_file, sheet_name="Sheet2")

ordinal_responses_map_pivot = (
    thresholds_df
    .pivot_table(index=["Risk Type", "Question No."],
                 columns="Ordinal Responses",
                 values="Threshold",
                 aggfunc="first")
    .rename(columns={1: "Threshold_1", 2: "Threshold_2", 3: "Threshold_3",
                     4: "Threshold_4", 5: "Threshold_5"})
    .reset_index()
)
for k in range(1, 6):
    col = f"Threshold_{k}"
    if col not in ordinal_responses_map_pivot.columns:
        ordinal_responses_map_pivot[col] = pd.NA


# ── Sum latent_y per scorecard/question ────────────────────────────────────

latent_y_df_sum_y = latent_y_df.groupby(["scorecard_seq_id", "q_join"]).agg({"latent_y": 'sum'})
sum_latent_y_df = latent_y_df.drop(columns=["Mev", f"mev_value_{TIMEPOINT}", "latent_y"])
unique_cols = ["scorecard_seq_id", "q_join"]
sum_latent_y_df = sum_latent_y_df.drop_duplicates(subset=unique_cols, keep="first")
sum_latent_y_df = sum_latent_y_df.merge(latent_y_df_sum_y, on=unique_cols, how="left").copy()

if DO_OUTPUT_DEBUG_FILE:
    sum_latent_y_df.to_csv(OUTPUT_DIR / "debug" / "sum_latent_y.csv", index=False)


# ── Compute stressed ordinal response ─────────────────────────────────────

ordinal_responses_map_pivot["Question No."] = ordinal_responses_map_pivot["Question No."].astype(str)
merged = sum_latent_y_df.merge(
    ordinal_responses_map_pivot, left_on="q_join", right_on="Question No.", how="left")

for k in range(1, 5):
    th = f"Threshold_{k}"
    merged[f"Prob>Threshold_{k}"] = 1 / (1 + np.exp(-(merged[th] - merged["latent_y"])))

merged["Prob(Stressed=1)"] = merged["Prob>Threshold_1"]
merged["Prob(Stressed=2)"] = merged["Prob>Threshold_2"] - merged["Prob>Threshold_1"]
merged["Prob(Stressed=3)"] = merged["Prob>Threshold_3"] - merged["Prob>Threshold_2"]
merged["Prob(Stressed=4)"] = merged["Prob>Threshold_4"] - merged["Prob>Threshold_3"]
merged["Prob(Stressed=5)"] = 1 - merged["Prob>Threshold_4"]

prob_cols = [f"Prob(Stressed={i})" for i in range(1, 6)]
merged[prob_cols] = merged[prob_cols].clip(lower=0)

if apply_score_distribution_not_max_prob_score:
    merged["upper_quantile"] = 1 + merged.groupby(['q_join', 'r_join'])['unstressed_qual_score'].rank(pct=True)
    merged["stressed_ordinal_response"] = np.where(
        merged["Beta"].notna(),
        np.where(merged["upper_quantile"] < merged["Prob>Threshold_1"], 1,
            np.where(merged["upper_quantile"] < merged["Prob>Threshold_2"], 2,
                np.where(merged["upper_quantile"] < merged["Prob>Threshold_3"], 3,
                    np.where(merged["Threshold_4"].notna(),
                        np.where(merged["upper_quantile"] < merged["Prob>Threshold_4"], 4, 5),
                        4)))),
        np.nan)
else:
    idx = merged[prob_cols].idxmax(axis=1)
    digits = idx.str.extract(r'(\d+)')[0]
    merged["stressed_ordinal_response"] = pd.to_numeric(digits, errors="coerce").astype("Int64")

output_df = merged[sum_latent_y_df.columns.tolist() + ["stressed_ordinal_response"]]
output_df = output_df.drop(columns=["Beta"])

if DO_OUTPUT_DEBUG_FILE:
    out_path1 = OUTPUT_DIR / "debug" / "stressed_ordinal_response.csv"
    output_df.to_csv(out_path1, index=False)


# ── Map ordinal to qualitative & compute impact ────────────────────────────

df = output_df.copy()
qual_map = {1: "A", 2: "B", 3: "C", 4: "D", 5: "E"}
df["stressed_qual_response"] = df["stressed_ordinal_response"].map(qual_map)

rev_qual_map = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}
df['ordinal_response'] = np.where(df['ordinal_response'].isna(),
                                   df['r_join'].map(rev_qual_map),
                                   df['ordinal_response'])

df["Response Change"] = df["stressed_ordinal_response"] - df["ordinal_response"]
df["Category"] = np.where(
    df["Response Change"].notna(),
    np.where(df["Response Change"] > 0, "Downgrade",
    np.where(df["Response Change"] < 0, "Upgrade", "Flat")),
    pd.NA)

out_path2 = OUTPUT_DIR / f"{scenario_name}_{TIMEPOINT}_stressed_responses.csv"
df.to_csv(out_path2, index=False)

n_deals = len(df['main_profile_leid'].unique())
df_factor_impact = df.groupby(["non_fin_ques_type", "q_join", "Category"]).agg({"main_profile_leid": "count"})
df_factor_impact['main_profile_leid'] = df_factor_impact['main_profile_leid'] / n_deals
df_factor_impact = df_factor_impact.pivot_table(
    index=["non_fin_ques_type", "q_join"], columns="Category", values=["main_profile_leid"])
fi_cols = df_factor_impact.columns
new_fi_cols = [first if second == "" else second for first, second in fi_cols.values]
df_factor_impact.columns = new_fi_cols
df_factor_impact["Factor"] = df_factor_impact['non_fin_ques_type'] + "_" + df_factor_impact['q_join']
df_factor_impact = df_factor_impact.drop(columns=['non_fin_ques_type', 'q_join'])
df_factor_impact = df_factor_impact[["Factor", "Downgrade", "Flat", "Upgrade"]]

out_path3 = OUTPUT_DIR / f"{scenario_name}_{TIMEPOINT}_factor_impact.csv"
df_factor_impact.to_csv(out_path3, index=False)

if COMPARE_OUTPUT:
    compare_csv(out_path2)
    compare_csv(out_path3)


# ── Fill missing stressed_qual_response ────────────────────────────────────

df = pd.read_csv(OUTPUT_DIR / f"{scenario_name}_{TIMEPOINT}_stressed_responses.csv")
df["stressed_qual_response"] = df["stressed_qual_response"].replace("", pd.NA)
df["r_join"] = df["r_join"].replace("", pd.NA)

r_lookup = (
    df.dropna(subset=["r_join"])
    .drop_duplicates(subset=["scorecard_seq_id", "q_join"], keep="last")
    .set_index(["scorecard_seq_id", "q_join"])["r_join"]
)
df["_r_fill"] = df.set_index(["scorecard_seq_id", "q_join"]).index.map(r_lookup)
df["stressed_qual_response_new"] = df["stressed_qual_response"].fillna(df["_r_fill"])
df = df.drop(columns=["_r_fill"])

if DO_OUTPUT_DEBUG_FILE:
    df.to_csv(OUTPUT_DIR / "debug" / "stressed_response_updated.csv", index=False)


# ── Merge PD data ──────────────────────────────────────────────────────────

stressed_with_weights = df.copy()
pd_data = pd.read_csv(MISC_INPUT_DIR / "sf_pd_data.csv")
pd_keep = pd_data[["scorecard_seq_id", "combined_crg", "offtake_pd", "offtake_crg", "loan_purpose"]].copy()
stressed_with_weights["scorecard_seq_id"] = stressed_with_weights["scorecard_seq_id"].astype(str)
pd_keep["scorecard_seq_id"] = pd_keep["scorecard_seq_id"].astype(str)
stressed_with_weights = stressed_with_weights.drop(columns=["offtake_pd", "offtake_crg", "loan_purpose"], errors="ignore")
stressed_with_weights = stressed_with_weights.merge(pd_keep, on="scorecard_seq_id", how="left")

if DO_OUTPUT_DEBUG_FILE:
    stressed_with_weights.to_csv(OUTPUT_DIR / "debug" / "stress_pd_data_merge.csv", index=False)


# ── Compute stressed qual score ────────────────────────────────────────────

final = stressed_with_weights.copy()
score_mapping = pd.read_excel(STATIC_INPUT_DIR / "Mapping_response.xlsx")
score_mapping[["non_fin_ques_no", 'non_fin_res_id']] = score_mapping[["non_fin_ques_no", 'non_fin_res_id']].astype(str)
final = final.merge(score_mapping, how='left',
                    left_on=['q_join', 'stressed_qual_response_new'],
                    right_on=['non_fin_ques_no', 'non_fin_res_id'])
final = final.rename(columns={"non_fin_res_score": "stressed_score"})
final['stressed_score'] = pd.to_numeric(final['stressed_score'], errors='coerce').fillna(0.0)
final['weighted_score'] = final['qual_res_weight2'] * final['stressed_score']

_nonzero = final[final['weighted_score'] != 0]
qual_score = _nonzero.groupby('scorecard_seq_id', as_index=False)['weighted_score'].sum()
qual_score.rename(columns={'weighted_score': 'qual_score'}, inplace=True)
qual_score['qual_score'] = qual_score['qual_score'].round(5)
final = pd.merge(final, qual_score, on='scorecard_seq_id', how='left')
final['qual_score'] = final['qual_score'].fillna(0.0)

if DO_OUTPUT_DEBUG_FILE:
    final.to_csv(OUTPUT_DIR / "debug" / "qual_score.csv", index=False)


# ── CG lookup & PD calculation ─────────────────────────────────────────────

final['unstressed_qual_score'] = pd.to_numeric(final['unstressed_qual_score'], errors='coerce').fillna(0.0)
final['qual_score'] = pd.to_numeric(final['qual_score'], errors='coerce').fillna(0.0)

lk = pd.read_csv(STATIC_INPUT_DIR / "cg_pd.csv")
lk['cg_look_up'] = lk['cg_look_up'].astype(str).str.strip().str.upper()


def calculate_unstressed_qual_pd(row):
    if row['loan_purpose'] == 'Post-Delivery Only':
        a, b = 6.483, 0.032
    elif row['loan_purpose'] == 'PrexPost-Delivery':
        a, b = 5.233, 0.010
    else:
        return None
    return 1 / (1 + np.exp(a + b * row['unstressed_qual_score']))


def calculate_qual_pd(row):
    if row['loan_purpose'] == 'Post-Delivery Only':
        a, b = 6.483, 0.032
    elif row['loan_purpose'] == 'PrexPost-Delivery':
        a, b = 5.233, 0.010
    else:
        return None
    return 1 / (1 + np.exp(a + b * row['qual_score']))


final['unstressed_qual_pd'] = final.apply(calculate_unstressed_qual_pd, axis=1)
final['qual_pd'] = final.apply(calculate_qual_pd, axis=1)


def lookup_cg(pd_val):
    row = lk[(pd_val >= lk['lower_bound']) & (pd_val <= lk['upper_bound'])]
    if not row.empty:
        return row.iloc[0]['cg_num'], row.iloc[0]['cg_look_up']
    return None, None


un_qual_num, un_qual_cg = zip(*[lookup_cg(v) for v in final['unstressed_qual_pd']])
qual_num, qual_cg = zip(*[lookup_cg(v) for v in final['qual_pd']])

final['unstressed_qual_cg_num'] = list(un_qual_num)
final['unstressed_qual_cg'] = list(un_qual_cg)
final['qual_cg_num'] = list(qual_num)
final['qual_cg'] = list(qual_cg)

final["Qual Difference in Notches"] = (final["qual_cg_num"] - final["unstressed_qual_cg_num"]) / 2
final["Qual Impact_Indicator"] = np.where(final["Qual Difference in Notches"] > 0, "Downgrade",
                                           np.where(final["Qual Difference in Notches"] < 0, "Upgrade", "Flat"))
final["Category_Qual"] = np.where(
    final["Qual Difference in Notches"] >= 3.5, ">= 3.5 notches",
    np.where(final["Qual Difference in Notches"] >= 2, "between 2-3 notches",
    np.where(final["Qual Difference in Notches"] > 0, "<=1.5 notches",
    np.where(final["Qual Difference in Notches"] < 0, "Upgrade", "Flat"))))

final = final.drop_duplicates(subset="main_profile_leid")

if DO_OUTPUT_DEBUG_FILE:
    final.to_csv(OUTPUT_DIR / "debug" / "qual_pd.csv", index=False)

df_KeyTable_QualCG = output_summary_table(final, "QualCG", "QualCG_impact",
    "Qual Impact_Indicator", "Category_Qual", outputIndividualFile=outputIndividualFile)

final_postDelivOnly = final[final['loan_purpose'] == 'Post-Delivery Only']
df_KeyTable_QualCGpostDelOnly = output_summary_table(
    final_postDelivOnly, "QualCGpostDelOnly", "QualCG_impact_postDelOnly",
    "Qual Impact_Indicator", "Category_Qual", outputIndividualFile=outputIndividualFile)

final_prePostDeliv = final[final['loan_purpose'] == 'PrexPost-Delivery']
df_KeyTable_QualCGprePostDeliv = output_summary_table(
    final_prePostDeliv, "QualCGprePostDeliv", "QualCG_impact_prePostDeliv",
    "Qual Impact_Indicator", "Category_Qual", outputIndividualFile=outputIndividualFile)


# ── OFFTAKER ───────────────────────────────────────────────────────────────

qual = final.copy()
charterer_path_xlsx = CHARTERER_CG_INPUT_DIR / f"Charterer_CG_list_{scenario_name}_{TIMEPOINT}.xlsx"
if os.path.exists(charterer_path_xlsx):
    oft = pd.read_excel(charterer_path_xlsx)
else:
    charterer_path_csv = CHARTERER_CG_INPUT_DIR / f"Charterer_CG_list_{scenario_name}_{TIMEPOINT}.csv"
    oft = pd.read_csv(charterer_path_csv)

pd_table = pd.read_csv(STATIC_INPUT_DIR / "cg_pd.csv")
s_pd = pd.read_csv(MISC_INPUT_DIR / "sf_pd_data.csv")
oft.columns = oft.columns.str.strip().str.lower()

oft['offtkr_stress_final_pd1'] = oft.groupby('scorecard_seq_id')['offtkr_stress_wt_pd'].transform('sum')
oft['offtkr_unstress_final_pd1'] = oft.groupby('scorecard_seq_id')['offtkr_unstress_wt_pd'].transform('sum')
oft['offtkr_stress_final_pd1'] = pd.to_numeric(oft['offtkr_stress_final_pd1'], errors='coerce')
oft['offtkr_unstress_final_pd1'] = pd.to_numeric(oft['offtkr_unstress_final_pd1'], errors='coerce')
pd_table['lower_bound'] = pd.to_numeric(pd_table['lower_bound'], errors='coerce')
pd_table['upper_bound'] = pd.to_numeric(pd_table['upper_bound'], errors='coerce')


def get_cg(pd_val):
    row = pd_table[(pd_table['lower_bound'] <= pd_val) & (pd_table['upper_bound'] > pd_val)]
    if not row.empty:
        return row['cg_look_up'].values[0]
    return None


oft['unstress_cg'] = oft['offtkr_unstress_final_pd1'].apply(get_cg)
oft['stress_cg'] = oft['offtkr_stress_final_pd1'].apply(get_cg)

qual['scorecard_seq_id'] = qual['scorecard_seq_id'].astype(str).str.strip()
oft['scorecard_seq_id'] = oft['scorecard_seq_id'].astype(str).str.strip()
oft = oft.drop_duplicates(subset='scorecard_seq_id')
out = qual.merge(oft, on='scorecard_seq_id', how='left')

out['stressed_offtkr_crg'] = out['stress_cg'].fillna(out['combined_crg'])
out['unstressed_offtkr_crg'] = out['unstress_cg'].fillna(out['combined_crg'])

s_pd["scorecard_seq_id"] = s_pd["scorecard_seq_id"].astype(str).str.strip()
spd_subset = s_pd[["scorecard_seq_id", "mcs_crg"]].drop_duplicates()
out = out.merge(spd_subset, on="scorecard_seq_id", how="left")

cond = out["mcs_crg"].notna() & (out["mcs_crg"] != "")
out.loc[cond, "stressed_offtkr_crg"] = out.loc[cond, "combined_crg"]
out.loc[cond, "unstressed_offtkr_crg"] = out.loc[cond, "combined_crg"]


# ── Model PD & final CG (standalone) ──────────────────────────────────────

df = out.copy()
lk = pd.read_csv(STATIC_INPUT_DIR / "cg_pd.csv")
df['stressed_offtkr_crg'] = df['stressed_offtkr_crg'].astype(str).str.strip().str.upper()
df['unstressed_offtkr_crg'] = df['unstressed_offtkr_crg'].astype(str).str.strip().str.upper()
lk['cg_look_up'] = lk['cg_look_up'].astype(str).str.strip().str.upper()

df['offtkr_stress_final_pd'] = df['stressed_offtkr_crg'].map(lk.set_index('cg_look_up')['pd'])
df['offtkr_unstress_final_pd'] = df['unstressed_offtkr_crg'].map(lk.set_index('cg_look_up')['pd'])

df['unstressed_model_pd'] = 0.5 * df['offtkr_unstress_final_pd'] + 0.5 * df['unstressed_qual_pd']
df['model_pd'] = 0.5 * df['offtkr_stress_final_pd'] + 0.5 * df['qual_pd']

unstressed_final_num, unstressed_final_cg_list = zip(*[lookup_cg(v) for v in df['unstressed_model_pd']])
final_num_list, final_cg_list = zip(*[lookup_cg(v) for v in df['model_pd']])

df['unstressed_final_cg_num'] = list(unstressed_final_num)
df['unstressed_final_cg'] = list(unstressed_final_cg_list)
df['final_cg_num'] = list(final_num_list)
df['final_cg'] = list(final_cg_list)

df["Difference in Notches"] = (df["final_cg_num"] - df["unstressed_final_cg_num"]) / 2
df["Impact_Indicator"] = np.where(df["Difference in Notches"] > 0, "Downgrade",
                                   np.where(df["Difference in Notches"] < 0, "Upgrade", "Flat"))
df["Category"] = np.where(
    df["Difference in Notches"] >= 3.5, ">= 3.5 notches",
    np.where(df["Difference in Notches"] >= 2, "between 2-3 notches",
    np.where(df["Difference in Notches"] > 0, "<=1.5 notches",
    np.where(df["Difference in Notches"] < 0, "Upgrade", "Flat"))))

df = df.drop_duplicates(subset="main_profile_leid")

standalone_output = OUTPUT_DIR / f"{scenario_name}_{TIMEPOINT}_standalone_cg.csv"
df.to_csv(standalone_output, index=False)
if COMPARE_OUTPUT:
    compare_csv(standalone_output)

df_KeyTable_StandaloneCG = output_summary_table(df, "StandaloneCG", "CG_impact",
    "Impact_Indicator", "Category", outputIndividualFile=outputIndividualFile)


# ── Warning signal ─────────────────────────────────────────────────────────

aws = pd.read_csv(MISC_INPUT_DIR / 'sf_warning_signal.csv', encoding="utf-8")
aws["downgraded_by"] = pd.to_numeric(aws["downgraded_by"], errors='coerce')
total_downgrades_by_scorecard = aws.groupby("scorecard_seq_id")["downgraded_by"].max().reset_index()
total_downgrades_by_scorecard.columns = ["scorecard_seq_id", "Total Downgrades"]

total_downgrades_by_scorecard["scorecard_seq_id"] = total_downgrades_by_scorecard["scorecard_seq_id"].astype(str).str.strip()
df["scorecard_seq_id"] = df["scorecard_seq_id"].astype(str).str.strip()
df_merged = df.merge(total_downgrades_by_scorecard[["scorecard_seq_id", "Total Downgrades"]],
                     on="scorecard_seq_id", how="left")
df_merged["Total Downgrades"] = df_merged["Total Downgrades"].fillna(0)

df_merged['aws_cg_num'] = df_merged['final_cg_num'] + (df_merged['Total Downgrades'] * 2)
df_merged['unstressed_aws_cg_num'] = df_merged['unstressed_final_cg_num'] + (df_merged['Total Downgrades'] * 2)


def map_aws_cg_num(val):
    if pd.isna(val):
        return np.nan
    val = int(val)
    if val <= 20:
        group = (val + 1) // 2
        suffix = 'A' if val % 2 == 1 else 'B'
    else:
        group = 11 + (val - 21) // 3
        suffix = ['A', 'B', 'C'][int(val - 21) % 3]
    return f"{group}{suffix}"


df_merged["Aftr_aws_crg"] = df_merged["aws_cg_num"].apply(map_aws_cg_num)
aws_cg_data = df_merged


# ── Parental support ───────────────────────────────────────────────────────

ps = pd.read_csv(MISC_INPUT_DIR / 'ps.csv', encoding="utf-8")
sc_sub_category = pd.read_csv(NEW_INPUT_DIR / 'sc_sub_category.csv', encoding="utf-8")
sovereign_ceiling_cor = pd.read_csv(NEW_INPUT_DIR / 'sovereign_ceiling_cor.csv', encoding="utf-8")
lcy_fcy = pd.read_csv(NEW_INPUT_DIR / 'lcy_fcy.csv', encoding="utf-8")
cntry_rating = pd.read_csv(NEW_INPUT_DIR / 'cntry_rating.csv', encoding="utf-8")

ps_data = ps[["scorecard_seq_id", "sc_parent_cr_id", "sc_recommended_crg", "sc_scorecard_crg",
              "sc_parent_crg", "sc_qual_cont_id", "sc_supported_crg",
              "sc_crg_domicile_contry", "sc_sub_category_id", "sc_crg_afc_cntry_ceiling",
              "sc_country_ceiling", "sc_parent_cap_applicable", "sc_final_appr_crg"]]

ps_data.columns = ps_data.columns.str.strip().str.lower()
sc_sub_category.columns = sc_sub_category.columns.str.strip().str.lower()

ps_data['sc_sub_category_id'] = ps_data['sc_sub_category_id'].astype(str).str.strip()
sc_sub_category['sc_sub_category_id'] = sc_sub_category['sc_sub_category_id'].astype(str).str.strip()

ps2 = ps_data.merge(sc_sub_category[['sc_sub_category_id']], on='sc_sub_category_id', how='left')

aws_cg_data.columns = aws_cg_data.columns.str.strip().str.lower()
ps2.columns = ps2.columns.str.strip().str.lower()

aws_cg_data['scorecard_seq_id'] = aws_cg_data['scorecard_seq_id'].astype(str).str.strip().str.upper()
ps2['scorecard_seq_id'] = ps2['scorecard_seq_id'].astype(str).str.strip().str.upper()
aws_cg_data['scorecard_seq_id'] = aws_cg_data['scorecard_seq_id'].str.replace('.0', '', regex=False)
ps2['scorecard_seq_id'] = ps2['scorecard_seq_id'].str.replace('.0', '', regex=False)

merge_ps_aws = pd.merge(aws_cg_data, ps2, on='scorecard_seq_id', how='left')

cor_cust = pd.read_csv(NEW_INPUT_DIR / "cor_cust_extract_dec_2024.csv")
cor_data = pd.read_excel(NEW_INPUT_DIR / "COR_GTGT.xlsx")

merge_ps_aws.columns = merge_ps_aws.columns.str.strip().str.lower()
cor_cust.columns = cor_cust.columns.str.lower()
cor_data.columns = cor_data.columns.str.lower()

merge_ps_aws['sc_parent_cr_id'] = merge_ps_aws['sc_parent_cr_id'].astype(str).str.strip()
cor_cust['cust_id'] = cor_cust['cust_id'].astype(str).str.strip()
merge_ps_aws['sc_parent_cr_id'] = merge_ps_aws['sc_parent_cr_id'].str.replace('.0', '', regex=False)
cor_cust['cust_id'] = cor_cust['cust_id'].str.replace('.0', '', regex=False)

cor_cust['ctry_of_risk'] = cor_cust['ctry_of_risk'].astype(str).str.strip().str.upper()
cor_data['cor'] = cor_data['cor'].astype(str).str.strip().str.upper()

parent_map = dict(zip(cor_cust['cust_id'], cor_cust['ctry_of_risk']))
merge_ps_aws['parent_cor'] = merge_ps_aws['sc_parent_cr_id'].map(parent_map)

sov_map = dict(zip(cor_data['cor'], cor_data['sov_stress_cg']))
merge_ps_aws['parent_sov_stress_cg'] = merge_ps_aws['parent_cor'].map(sov_map)

mask = (
    merge_ps_aws['parent_cor'].notna() &
    (merge_ps_aws['parent_cor'] != '') &
    (merge_ps_aws['cor'].isna() | (merge_ps_aws['cor'] == ''))
)
merge_ps_aws.loc[mask, 'parent_sov_stress_cg'] = merge_ps_aws.loc[mask, 'scb_rating']
merge_ps_aws.loc[mask, 'parent_bau_sov_cg'] = merge_ps_aws.loc[mask, 'scb_rating']

merge_ps_aws['child_sov_stress_cg'] = merge_ps_aws['ctry_of_risk'].map(sov_map)

parent_fill_mask = merge_ps_aws['sc_parent_crg'].notna() & merge_ps_aws['parent_sov_stress_cg'].isna()
merge_ps_aws.loc[parent_fill_mask, 'parent_sov_stress_cg'] = merge_ps_aws.loc[parent_fill_mask, 'sc_parent_crg']

child_fill_mask = merge_ps_aws['sc_crg_domicile_contry'].notna() & merge_ps_aws['child_sov_stress_cg'].isna()
merge_ps_aws.loc[child_fill_mask, 'child_sov_stress_cg'] = merge_ps_aws.loc[child_fill_mask, 'sc_crg_domicile_contry']


def cg_to_num(code):
    if pd.isna(code):
        return None
    code = str(code).lower().strip()
    if code in ['13', '14']:
        return 26 + (int(code) - 12)
    try:
        number = int(code[:-1])
        letter = code[-1]
    except:
        return None
    if number <= 10:
        return (number - 1) * 2 + (ord(letter) - ord('a')) + 1
    elif number in [11, 12]:
        return 20 + (number - 11) * 3 + (ord(letter) - ord('a')) + 1
    return None


merge_ps_aws['bau_sov_num'] = merge_ps_aws['bau_sov_cg'].apply(cg_to_num)
merge_ps_aws['parent_cg_num'] = merge_ps_aws['sc_parent_crg'].apply(cg_to_num)
merge_ps_aws['sov_ceiling_num'] = merge_ps_aws['sc_crg_domicile_contry'].apply(cg_to_num)
merge_ps_aws['parent_sov_stress_num'] = merge_ps_aws['parent_sov_stress_cg'].apply(cg_to_num)
merge_ps_aws['child_sov_stress_num'] = merge_ps_aws['child_sov_stress_cg'].apply(cg_to_num)

for c in ['parent_cg_num', 'parent_sov_stress_num', 'sov_ceiling_num', 'child_sov_stress_num']:
    merge_ps_aws[c] = pd.to_numeric(merge_ps_aws[c], errors='coerce')

mask_parent = merge_ps_aws['parent_cg_num'] > merge_ps_aws['parent_sov_stress_num']
merge_ps_aws.loc[mask_parent, 'parent_cg_num'] = merge_ps_aws.loc[mask_parent, 'parent_sov_stress_num']

merge_ps_aws["sc_sub_clean"] = (
    merge_ps_aws["sc_sub_category_id"].astype(str).str.strip().str.replace(".0", "", regex=False))

cond_8004 = merge_ps_aws["sc_sub_clean"] == "8004"
cond_blank = merge_ps_aws["sc_sub_clean"].isin(["", "nan", "None"])

merge_ps_aws["after_parent_stress_cg_num"] = merge_ps_aws['aws_cg_num']
merge_ps_aws.loc[cond_8004, "after_parent_stress_cg_num"] = merge_ps_aws.loc[cond_8004, 'parent_sov_stress_num']

cond_parent_worse = merge_ps_aws['parent_sov_stress_num'] > merge_ps_aws['aws_cg_num']
take_parent = (
    cond_blank &
    cond_parent_worse &
    (merge_ps_aws["sc_parent_cap_applicable"].astype(str).str.strip().str.upper() == "Y")
)
merge_ps_aws.loc[take_parent, "after_parent_stress_cg_num"] = merge_ps_aws.loc[take_parent, 'parent_sov_stress_num']

merge_ps_aws["after_parent_unstress_cg_num"] = merge_ps_aws['unstressed_aws_cg_num']
merge_ps_aws.loc[cond_8004, "after_parent_unstress_cg_num"] = merge_ps_aws.loc[cond_8004, "parent_cg_num"]

cond_parent_worse_un = merge_ps_aws['parent_cg_num'] > merge_ps_aws['unstressed_aws_cg_num']
take_parent_un = (
    cond_blank &
    cond_parent_worse_un &
    (merge_ps_aws["sc_parent_cap_applicable"].astype(str).str.strip().str.upper() == "Y")
)
merge_ps_aws.loc[take_parent_un, "after_parent_unstress_cg_num"] = merge_ps_aws.loc[take_parent_un, 'parent_cg_num']

mask_sov = merge_ps_aws['sov_ceiling_num'] > merge_ps_aws['child_sov_stress_num']
merge_ps_aws.loc[mask_sov, 'sov_ceiling_num'] = merge_ps_aws.loc[mask_sov, 'child_sov_stress_num']

for c in ['after_parent_stress_cg_num', 'child_sov_stress_num', 'after_parent_unstress_cg_num', 'sov_ceiling_num']:
    merge_ps_aws[c] = pd.to_numeric(merge_ps_aws[c], errors='coerce')

merge_ps_aws['after_sov_stress_cg_num'] = merge_ps_aws[
    ['after_parent_stress_cg_num', 'child_sov_stress_num']].max(axis=1)
merge_ps_aws['after_sov_unstress_cg_num'] = merge_ps_aws[
    ['after_parent_unstress_cg_num', 'sov_ceiling_num']].max(axis=1)

sov_ceiling = merge_ps_aws


# ── Apply overrides ────────────────────────────────────────────────────────

sov_ceiling["sc_recommended_crg"] = sov_ceiling["sc_recommended_crg"].astype(str)


def sov_final_cg_to_num(code):
    if pd.isna(code) or code == "nan":
        return None
    code = str(code).lower().strip()
    number = int(code[:-1])
    letter = code[-1]
    if number <= 10:
        return (number - 1) * 2 + (ord(letter) - ord('a')) + 1
    elif number in [11, 12]:
        return 20 + (number - 11) * 3 + (ord(letter) - ord('a')) + 1
    return None


sov_ceiling['sc_scorecard_crg_num'] = sov_ceiling['sc_scorecard_crg'].apply(sov_final_cg_to_num)
sov_ceiling['sc_recommended_crg_num'] = sov_ceiling['sc_recommended_crg'].apply(sov_final_cg_to_num)
sov_ceiling['sc_final_appr_crg_num'] = sov_ceiling['sc_final_appr_crg'].apply(sov_final_cg_to_num)

sov_ceiling['diff'] = sov_ceiling['sc_final_appr_crg_num'] - sov_ceiling['sc_scorecard_crg_num']
sov_ceiling["final_stress_cg_num"] = sov_ceiling["diff"] + sov_ceiling["after_sov_stress_cg_num"]
sov_ceiling["final_unstress_cg_num"] = sov_ceiling["diff"] + sov_ceiling["after_sov_unstress_cg_num"]
sov_ceiling["final_stress_cg_num"] = sov_ceiling["final_stress_cg_num"].clip(lower=1)
sov_ceiling["final_unstress_cg_num"] = sov_ceiling["final_unstress_cg_num"].clip(lower=1)


def num_to_grade(n):
    if pd.isna(n):
        return None
    n = int(n)
    if 1 <= n <= 20:
        level = (n - 1) // 2 + 1
        suffix = chr(ord('A') + (n - 1) % 2)
        return f"{level}{suffix}"
    elif 21 <= n <= 26:
        level = 11 + (n - 21) // 3
        suffix = chr(ord('A') + (n - 21) % 3)
        return f"{level}{suffix}"
    elif n == 27:
        return "13"
    elif n == 28:
        return "14"
    return None


sov_ceiling['after_parent_cg'] = sov_ceiling['after_parent_stress_cg_num'].apply(num_to_grade)
sov_ceiling['After_sov_stress_cg'] = sov_ceiling['after_sov_stress_cg_num'].apply(num_to_grade)
sov_ceiling['final_stress_cg'] = sov_ceiling['final_stress_cg_num'].apply(num_to_grade)
sov_ceiling['unstressed_after_parent_cg'] = sov_ceiling['after_parent_unstress_cg_num'].apply(num_to_grade)
sov_ceiling['After_sov_ceiling_unstress_cg'] = sov_ceiling['after_sov_unstress_cg_num'].apply(num_to_grade)
sov_ceiling['final_unstress_cg'] = sov_ceiling['final_unstress_cg_num'].apply(num_to_grade)


# ── Final output ───────────────────────────────────────────────────────────

final_crg_post_overrides = sov_ceiling
final_crg_post_overrides["final_stress_cg_num"] = pd.to_numeric(
    final_crg_post_overrides["final_stress_cg_num"], errors="coerce")

final_crg_post_overrides["Difference in Notches_post_overrides"] = (
    final_crg_post_overrides["final_stress_cg_num"] - final_crg_post_overrides["final_unstress_cg_num"])

final_crg_post_overrides["Impact_Indicator_post_overrides"] = np.where(
    final_crg_post_overrides["Difference in Notches_post_overrides"] > 0, "Downgrade",
    np.where(final_crg_post_overrides["Difference in Notches_post_overrides"] < 0, "Upgrade", "Flat"))

final_crg_post_overrides["Category_post_overrides"] = np.where(
    final_crg_post_overrides["Difference in Notches_post_overrides"] >= 3.5, ">= 3.5 notches",
    np.where(final_crg_post_overrides["Difference in Notches_post_overrides"] >= 2, "between 2-3 notches",
    np.where(final_crg_post_overrides["Difference in Notches_post_overrides"] > 0, "<=1.5 notches",
    np.where(final_crg_post_overrides["Difference in Notches_post_overrides"] < 0, "Upgrade", "Flat"))))

final_crg_post_overrides = final_crg_post_overrides.drop_duplicates(subset="main_profile_leid")

final_cg_output = OUTPUT_DIR / f"{scenario_name}_{TIMEPOINT}_final_cg.csv"
final_crg_post_overrides.to_csv(final_cg_output, index=False)

df_KeyTable_final_crg_post_overrides = output_summary_table(
    final_crg_post_overrides, "final_crg", "CG_impact",
    "Impact_Indicator_post_overrides", "Category_post_overrides",
    outputIndividualFile=outputIndividualFile)

df_KeyTable = pd.concat([
    df_KeyTable_QualCG,
    df_KeyTable_QualCGpostDelOnly,
    df_KeyTable_StandaloneCG,
    df_KeyTable_final_crg_post_overrides
])

df_KeyTable.to_csv(OUTPUT_DIR / f"{scenario_name}_{TIMEPOINT}_keyTable.csv", index=False)
