from config.SF_config import *

MEV_hist_PATH = PROJECT_DIR / "3. SF/1) Input/5) CG/4) HEV/Final HEV transformation_only internal HEVs_0704.csv"

MODEL_INPUTS = {
    "MGT": "Stress testing input(optim_all_70_offline_skip).xlsx",
}
MODEL_INPUTS = {k: PROJECT_DIR / "SF/3) CG/1) Input/1) Qual Factor" / v for k, v in MODEL_INPUTS.items()}

CG_RAW_SCENARIO_PATH = PROJECT_DIR / "3. SF/1) Input/5) CG/5) Scenario"
CG_OUTPUT_PATH = PROJECT_DIR / "6. Revised model" / "3. SF" / "2) Output" / "5) CG"

CG_Chart = {
    PROJECT_DIR / "SF/3) CG/2) Output/CG_Impact_Chart.xlsx"
}

Impact_Chart = {
    PROJECT_DIR / "SF/3) CG/2) Output/Chart_SF_DEAL_factor_impact.xlsx"
}

if OUTPUT_DIR_FINAL:
    TIMEPOINTS = ["p4"]
else:
    TIMEPOINTS = ["p4", "p8", "p12"]

SCENARIOS = {
    "BGTT": CG_RAW_SCENARIO_PATH / "SPLICE_PICST_Stress_11112024.csv",
    "GTGT": CG_RAW_SCENARIO_PATH / "GTGT_ICAAP_2025_Splice_upload_04112024v2.csv",
    "BOE": CG_RAW_SCENARIO_PATH / "BOE_ACS.csv",
    "ACSRF": CG_RAW_SCENARIO_PATH / "ICAAP_ACSRf.csv",
    "CSGD": CG_RAW_SCENARIO_PATH / "CSGD.csv",
    "EMGT": CG_RAW_SCENARIO_PATH / "EMGT.csv",
}

SCENARIOS_date = {
    "BGTT": "2024-09-30",
    "GTGT": "2024-09-30",
    "BOE": "2022-06-30",
    "ACSRF": "2023-09-30",
    "CSGD": "2024-12-31",
    "EMGT": "2023-09-30",
}
