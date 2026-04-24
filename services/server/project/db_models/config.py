# uam
ROLES_FILE = 'project/data/db/Roles.csv'
# ROLEPERMISSIONS_FILE = 'project/data/db/RolePermissions.csv'
# cem
IAM_PATHWAYS_FILE = 'project/data/db/IAMPathways_v2.csv'
IAM_MAPPING_SECTOR_FILE = 'project/data/db/IAMMappingSector.csv'
INTENSITIES_FILE = 'project/data/db/Intensity.csv'
TAX_FILE = 'project/data/db/Tax.csv'
COUNTRY_FILE = 'project/data/db/Country.csv'
PD_CALIBRATE_FILE = 'project/data/db/PD_Calibrate_CP.csv'
KBLI_CODE_FILE = 'project/data/db/KBLI_Code.csv'
SECTOR_ELASTICITY_FILE = 'project/data/db/Sector Elasticity.csv'
# bottomup
IAM_BOTTOMUP_PATHWAYS_FILE = 'project/data/db/IAM Bottomup Pathways.csv'
BOTTOMUP_SECTORS_FILE = 'project/data/db/BottomupSectors.csv'
# macro
MACRO_ECONOMIC_DATA_FILE = 'project/data/db/MacroData_v2.csv'
STRESSED_MACRO_ECONOMIC_DATA_FILE = 'project/data/db/StressedMacroData.csv'
# sme
SME_SECTOR_MAPPING_FILE = 'project/data/db/Sector Mapping.csv'
SME_COMPOSITION_FILE = 'project/data/db/SME-Composition.csv'
# netzero
TEMPERATURE_ALIGNMENT_REGRESSION_FILE = 'project/data/db/Temperature_REGRESSION_PARAM.csv'
# frtb
FRTB_PARAMETERS_FILE = 'project/data/db/FRTB-Parameters.csv'
FRTB_RISK_WEIGHT_FILE = 'project/data/db/FRTB-RiskWeight.csv'
FRTB_BASECURVE_FILE = 'project/data/db/FRTB-BaseCurve.csv'
FRTB_EQUITYSPOT_FILE = 'project/data/db/FRTB-EquitySpot.csv'
FRTB_FXSPOT_FILE = 'project/data/db/FRTB-FXSpot.csv'
FRTB_COMMODITYSPOT_FILE = 'project/data/db/FRTB-CommoditySpot.csv'
FRTB_CROSS_CURRENCY_BASIS_FILE = 'project/data/db/FRTB-CrossCurrencyBasis.csv'
FRTB_CREDITSPREAD_FILE = 'project/data/db/FRTB-CreditSpread.csv'
# physical
CITY_BOUNDARY_FILE = 'project/data/db/City Boundary.csv'
IRBI_INDEX_FILE = 'project/data/db/IRBI_Index.csv'
IRBI_FWD_CACHE_FILE = 'project/data/db/IRBI_Fwd_Cache.csv'
FLOOD_FWD_CACHE_FILE = 'project/data/db/Flood Impact Cache.csv'
TC_HAZARD_DATA_FILE = 'project/data/db/TC_history_track.csv'
# PCAF
PCAFBusinessLoanUnlistedEquityOption2a_FILE = 'project/data/db/pcaf/BusinessLoansUnlistedEquityOption2a.csv'
PCAFBusinessLoanUnlistedEquityOption2b_FILE = 'project/data/db/pcaf/BusinessLoansUnlistedEquityOption2b.csv'
PCAFBusinessLoanUnlistedEquityOption3_FILE = 'project/data/db/pcaf/BusinessLoansUnlistedEquityOption3.csv'
PCAFHeavyDutyVehicleOption1a_FILE = 'project/data/db/pcaf/HeavyDutyVehicleOption1a.csv'
PCAFHeavyDutyVehicleOption1b_FILE = 'project/data/db/pcaf/HeavyDutyVehicleOption1b.csv'
PCAFListedEquityAndCorporateBondsOption2a_FILE = 'project/data/db/pcaf/ListedEquityAndCorporateBondsOption2a.csv'
PCAFListedEquityAndCorporateBondsOption2b_FILE = 'project/data/db/pcaf/ListedEquityAndCorporateBondsOption2b.csv'
PCAFListedEquityAndCorporateBondsOption3_FILE = 'project/data/db/pcaf/ListedEquityAndCorporateBondsOption3.csv'
PCAFMortgageCommercialResidentialOption1_FILE = 'project/data/db/pcaf/MortgageCommercialResidentialOption1.csv'
PCAFMortgageCommercialResidentialOption2_FILE = 'project/data/db/pcaf/MortgageCommercialResidentialOption2.csv'
PCAFMortgageCommercialResidentialOption3_FILE = 'project/data/db/pcaf/MortgageCommercialResidentialOption3.csv'
PCAFSeaAndAirOption1a_FILE = 'project/data/db/pcaf/SeaAndAirOption1a.csv'
PCAFSeaAndAirOption1b_FILE = 'project/data/db/pcaf/SeaAndAirOption1b.csv'
PCAFMotorVehicleLoansOption1_FILE = 'project/data/db/pcaf/MotorVehicleLoansOption1.csv'
PCAFMotorVehicleLoansOption2_FILE = 'project/data/db/pcaf/MotorVehicleLoansOption2.csv'
PCAFMotorVehicleLoansOption3_FILE = 'project/data/db/pcaf/MotorVehicleLoansOption3.csv'
PCAFSovereignGHGEmission_FILE = 'project/data/db/pcaf/SovereignGHGEmission.csv'
PCAFSovereignGHGGDP_FILE = 'project/data/db/pcaf/SovereignGHGGDP.csv'

FILES_TO_RELOAD = {
    IAM_PATHWAYS_FILE: ['cem-corporate'],
    INTENSITIES_FILE: ['cem-corporate'],
    KBLI_CODE_FILE: ['cem-corporate'],
    SECTOR_ELASTICITY_FILE: ['cem-corporate'],
    IAM_BOTTOMUP_PATHWAYS_FILE: ['bottomup-corporate'],
    MACRO_ECONOMIC_DATA_FILE: ['frtb-market'],
    STRESSED_MACRO_ECONOMIC_DATA_FILE: ['frtb-riskweight']
}
