# Comparative Advantage in AI: Factor Content of Trade Analysis

This repository contains Python scripts for constructing labour, capital, patent, and factor content of trade datasets to analyse comparative advantage in AI-patents using the Heckscher-Ohlin-Vanek (HOV) framework.

## Overview

This project examines the role of accumulated AI-related knowledge in shaping countries' comparative advantage in international trade from 2010-2021, with particular focus on the EU's position relative to the US and China. The analysis employs an extended Heckscher-Ohlin-Vanek (HOV) framework incorporating AI patent stocks, non-AI patent stocks, labour, and capital as production factors.

The empirical implementation follows the methodology of Trefler and Zhu (2010), using inter-country input-output (IIO) tables from Eurostat's FIGARO database to account for global value chains and cross-country technological differences.

## Repository Structure

```
ca_in_ai/
├── labour/          # Employment data processing (8 scripts)
├── capital/         # Capital stock estimation (12 scripts)
├── patent/          # Patent data processing and stock construction (17 scripts)
├── fct/             # Factor content of trade calculations and tests (43 scripts)
└── requirements.txt # Python package dependencies
```

## Data Sources

- **Employment:** OECD Trade in Employment (TIM), Eurostat National Accounts, World Bank WDI
- **Capital:** OECD STAN, Penn World Tables 10, UK ONS, China KLEMS, India KLEMS, Swiss Federal Statistics
- **Patents:** WIPO PATENTSCOPE database (PCT applications)
- **Input-Output:** Eurostat FIGARO 2025 edition (45 countries, 64 industries, 2010-2021)

## Labour Scripts (8 scripts)

Process employment data from multiple sources to construct industry-level labour endowments for 45 countries plus rest of world (2010-2021), following the methodology of Labaj et al. (2023).

1. **`1_transform_TIM.py`** - Transforms TIM database from long format to structured panel format, standardising country and industry codes to ensure consistency with Figaro classification
2. **`2_Figaro_IO_Update.py`** - Updates latest 2025 edition Figaro input-output tables to exclude data for Albania, Montenegro, North Macedonia, and Serbia
3. **`3_labor_consolidation_2022_recreate.py`** - Recreates the methodology of Labaj et al. (2023) for producing final labour files as baseline reference
4. **`4_labor_consolidation_2025.py`** - Merges employment data from TIM with Figaro industry classifications, imputes missing values using industry-level patterns, and reconciles discrepancies between data sources
5. **`5_labor_WDI_employment.py`** - Integrates aggregate country-level employment totals from World Development Indicators to validate and adjust industry-disaggregated employment figures
6. **`6_labor_summary.py`** - Produces descriptive statistics including employment levels by country and industry, growth rates, and coverage statistics
7. **`7_labour_country_visuals.py`** - Generates comparative figures showing employment distributions across countries and temporal trends
8. **`8_labour_industry_visuals.py`** - Creates visualisations of employment distributions across industries and temporal trends in employment composition

## Capital Scripts (12 scripts)

Construct net capital stock estimates at industry-country level using data from OECD STAN, Penn World Tables, and national statistical offices, with extensive imputation procedures.

1. **`0_filter_OECD_STAN_data.py`** - Filters OECD STAN database to extract relevant variables and ensure consistency with Figaro industry classification
2. **`0_pivot_OECD_STAN_data.py`** - Reshapes OECD STAN data from long to wide format to facilitate subsequent imputation procedures
3. **`0_pivot_pwt_data.py`** - Reshapes Penn World Tables data from long to wide format with separate pivoting operations for different PWT subsets
4. **`0_pivot_pwt_data_figw1.py`** - Performs additional pivoting operations on PWT data for specific country groupings
5. **`1_capital_stock_impute_bucket1.py`** - Implements primary imputation using capital intensity of countries with available industry-level net capital stock data to estimate missing observations for other countries
6. **`2_capital_stock_impute_CN.py`** - Applies specialised imputation procedure for China where data limitations necessitate alternative estimation methods
7. **`3_capital_stock_impute_bucket2.py`** - Performs second round of imputation for remaining missing values using cross-country industry averages
8. **`4_capital_stock_validate.py`** - Conducts diagnostic tests on imputed capital stock series, comparing estimated values against available benchmarks and checking for internal consistency
9. **`5_capital_factor_vector.py`** - Transforms validated capital stock data into factor endowment vectors suitable for factor content of trade calculations
10. **`6_capital_summary.py`** - Generates descriptive statistics on capital stocks and capital intensity across countries and industries
11. **`7_capital_country_visuals.py`** - Creates comparative visualisations of capital stock endowments across countries
12. **`8_capital_industry_visuals.py`** - Produces comparative visualisations of capital stock endowments across industries

## Patent Scripts (17 scripts)

Process PCT patent applications from WIPO PATENTSCOPE database to identify AI-related patents, construct patent stocks using perpetual inventory method (15% depreciation), and map to NACE Rev.2 industries.

1. **`0_initial_descriptives.py`** - Loads patent data from multiple patent offices (PCT, USPTO, EPO, JPO, KR, CN) and creates time series visualisations comparing PCT application volumes with national office filings and grant rates
2. **`1_patent_consolidation.py`** - Consolidates individual country patent files into unified database, extracting IPC4 codes and standardising identifiers while removing duplicates
3. **`2_ai_patent_consolidation.py`** - Processes AI-specific patent data from WIPO's two query segments (CPC-based and keyword-based) and merges them into single AI patent dataset
4. **`3_patent_and_ipc_weights.py`** - Calculates patent weights (inverse of applicant count per patent) and IPC4 weights (inverse of IPC4 code count per patent) for fractional allocation
5. **`4_patent_country_year_aggregate.py`** - Aggregates weighted patent counts by applicant residence country and application year
6. **`5_patent_industry_aggregate.py`** - Maps patents to NACE Rev.2 industries using IPC-to-ISIC concordance following Lybbert and Zolas (2014), applying fractional weights across multiple technology-industry assignments
7. **`6_non_ai_count_country.py`** - Computes non-AI patent counts by subtracting AI patents from total PCT patents at country level
8. **`7_non_ai_count_industry.py`** - Computes non-AI patent counts by subtracting AI patents from total PCT patents at industry level
9. **`8_patent_stock_country.py`** - Applies perpetual inventory method with 15% annual depreciation to construct patent stocks from application flows for country-year observations
10. **`9_patent_stock_industry.py`** - Applies perpetual inventory method with 15% annual depreciation to construct patent stocks for country-industry-year observations
11. **`10_patent_country_summary_tables.py`** - Generates descriptive statistics tables for patent stocks and flows aggregated by country
12. **`11_patent_industry_summary_tables.py`** - Produces summary tables for patent data disaggregated by industry
13. **`12_patent_country_visuals.py`** - Creates visualisations of patent stocks, growth rates, and AI intensity by country
14. **`13_patent_industry_visuals.py`** - Generates visualisations of patent stocks, growth rates, and AI intensity by industry
15. **`14_ai_patent_factor_vector.py`** - Transforms AI patent stock data into factor requirement matrices compatible with FIGARO IIO structure for FCT calculations
16. **`15_non_ai_patent_factor_vector.py`** - Transforms non-AI patent stock data into factor requirement matrices compatible with FIGARO IIO structure
17. **`16_patent_depreciation_robustness.py`** - Recalculates patent stocks under alternative depreciation rates to test sensitivity of results to baseline 15% assumption

## Factor Content of Trade Scripts (43 scripts)

Implement HOV framework to compute measured and predicted factor content of trade, perform statistical tests, and conduct robustness analysis.

1. **`0_factor_shares.py`** - Visualises distribution of factor cost shares in value added across countries and time
2. **`0_us_china_eu_2010.py`** - Creates focused visualisations of factor shares for US, China, and EU for benchmark year 2010
3. **`0_us_china_eu_2021.py`** - Creates focused visualisations of factor shares for US, China, and EU for benchmark year 2021
4. **`1_gross_output.py`** - Extracts gross output by country-industry from FIGARO IIO tables and aggregates across all years into single file
5. **`2_value_added.py`** - Extracts value added by country-industry from FIGARO tables for all years
6. **`3_net_trade_vector.py`** - Computes net export vectors for each country-industry-year combination from FIGARO bilateral trade flows
7. **`4_factor_vector.py`** - Assembles complete factor endowment matrix by stacking AI patents, non-AI patents, labour, and capital data for each country-industry-year, normalised by gross output
8. **`5_leontief_inverse.py`** - Computes technical coefficients matrix A from FIGARO IIO data and calculates Leontief inverse L = (I-A)^-1 for each year
9. **`5_leontief_validity_check.py`** - Verifies that computed Leontief inverse satisfies identity A·L = L·A = L - I as diagnostic check
10. **`6_measured_fct.py`** - Computes measured factor content of trade using equation f^c = e'·L·T^c
11. **`7_shares.py`** - Computes countries' consumption shares σ^c from GDP and trade balance data for use in predicted FCT calculations
12. **`8_factor_endowments.py`** - Aggregates industry-level factor data to construct country-level factor endowment vectors V^c
13. **`9_predicted_fct.py`** - Computes predicted factor content of trade using Vanek equation F^c = V^c - σ^c·V^W for each country and year
14. **`10_eu_fct_agg.py`** - Aggregates measured FCT, predicted FCT, and consumption shares across EU27 member states to treat EU as single economic entity
15. **`11_factor_wise_fct.py`** - Decomposes factor content calculations by individual factors, computing sign consistency between measured and predicted values for each factor separately
16. **`12_fct_tests.py`** - Implements sign tests, rank tests, and regression analysis following Trefler (1995) to evaluate HOV model performance aggregated across all countries
17. **`12_fct_tests_country_level.py`** - Performs sign tests, rank tests, and regression analysis disaggregated by individual country
18. **`13A_single_factor_abundance_PCT_ALL.py`** - Computes single-factor abundance measures for all PCT applications
19. **`13B_relative_factor_abundance_PCT_ALL.py`** - Calculates relative factor abundance indices comparing AI to non-AI patents following Leamer (1980) for all PCT applications
20. **`13C_single_factor_abundance_PCT_NATIONAL.py`** - Computes single-factor abundance measures for PCT applications that have entered national phases
21. **`13D_relative_factor_abundance_PCT_NATIONAL.py`** - Calculates relative factor abundance indices for PCT applications that have entered national phases
22. **`14A_plot_single_factor_abundance_PCT_All.py`** - Generates time series visualisations of single-factor abundance for all PCT applications
23. **`14B_plot_relative_factor_abundance_PCT_ALL.py`** - Creates time series visualisations of relative factor abundance for all PCT applications
24. **`14C_plot_single_factor_abundance_PCT_NATIONAL.py`** - Produces time series visualisations of single-factor abundance for national-phase PCT applications
25. **`14D_plot_relative_factor_abundance_PCT_NATIONAL.py`** - Generates time series visualisations of relative factor abundance for national-phase PCT applications
26. **`15_patent_investment_comparasion.py`** - Compares AI patent per capita with AI investment per capita in EU for plausibility check
27. **`16_fct_robustness_test.py`** - Re-estimates baseline HOV tests for patent stocks calculated with different depreciation rates
28. **`17_rfa_robustness_all.py`** - Recalculates relative factor abundance under alternative depreciation rates for all PCT applications
29. **`18_rfa_robustness_national.py`** - Recalculates relative factor abundance under alternative depreciation rates for PCT applications entering national phase
30. **`18_rfa_robustness_agg_2021.py`** - Produces summary table comparing relative factor abundance values for 2021 across all depreciation rate specifications
31. **`19_fct_sensitivity_calculations.py`** - Implements sensitivity analysis by excluding each of 64 industries in turn and recalculating factor vectors, Leontief inverse, net trade vectors, and measured FCT
32. **`20_fct_sensitivity_eu_agg.py`** - Aggregates EU27 countries for each industry-exclusion sensitivity specification
33. **`21_fct_sensitivity_rfa_tests.py`** - Computes relative factor abundance for each industry-exclusion specification
34. **`21_fct_sensitivity_rfa_tests_combine.py`** - Compiles relative factor abundance results across all 64 sensitivity tests to assess robustness
35. **`22_fct_sensitivity_treffler_tests.py`** - Implements industry-variance decomposition tests following methodology of Trefler and Zhu (2010)
36. **`22_fct_sensitivity_treffler_tests_agg_industry_variance.py`** - Analyses industry-level variance contributions to identify which industries contribute most to deviations between measured and predicted factor content
37. **`23_fct_sensitivity_non_tradable_tests.py`** - Tests improvements of HOV fit by re-running HOV tests after removing high-variance industries

## Installation

### Requirements

- Python 3.8 or higher
- NumPy (1.21+)
- pandas (1.3+)
- matplotlib (3.4+)
- scipy (1.7+)
- statsmodels (0.13+)

### Setup

```bash
# Clone repository
git clone https://github.com/nikhil-megh/ca_in_ai.git
cd ca_in_ai

# Install dependencies
pip install -r requirements.txt
```

## Usage

Scripts follow systematic numbering convention where each numbered script performs operations used by subsequent scripts.

**IMPORTANT:** Scripts contain hard-coded file paths that must be modified to match your local directory structure before execution.

### Execution Order

1. **Labour data:** `1→2→3→4→5→6→7→8`
2. **Capital data:** `0 (all three)→1→2→3→4→5→6→7→8`
3. **Patent data:** `0→1→2→3→4→5→6→7→8→9→10→11→12→13→14→15→16`
4. **FCT analysis:** `0 (all three)→1→2→3→4→5→6→7→8→9→10→11→12→13→14→15→16→17→18→19→20→21→22→23`

## Methodology

### Patent Stock Construction

Patents are assigned to countries by applicant residence and mapped to NACE Rev.2 industries using Lybbert-Zolas (2014) IPC-to-ISIC concordance. Patent stocks are constructed using perpetual inventory method:

```
S_t = (1 - δ)·S_{t-1} + F_t
```

where δ = 0.15 (baseline), initialized in the year 2000.

### Factor Content of Trade

**Measured FCT:** Calculated following Trefler and Zhu (2010):
```
f^c = E·L·T^c
```
where E is factor intensity matrix, L is Leontief inverse, T^c is net trade vector.

**Predicted FCT:** Calculated using Vanek equation:
```
F^c = V^c - σ^c·V^W
```
where V^c is country factor endowment, σ^c is consumption share, V^W is world endowment.

**Statistical Tests:** Sign tests, rank tests, and regression analysis following Leamer (1980) and Trefler (1995).

**Comparative Advantage:** Relative factor abundance indices following Leamer (1980):
```
RFA^AI = (V^AI/V^non-AI) / (C^AI/C^non-AI)
```

## Key References

- Eurostat (2025). Macroeconomic Globalisation Indicators based on FIGARO (2025 edition). Available at: https://ec.europa.eu/eurostat/web/esa-supply-use-input-tables/database
- Feenstra, R.C., Inklaar, R., & Timmer, M.P. (2015). The Next Generation of the Penn World Table. American Economic Review, 105(10), 3150-3182.
Johnson, D. (2002). The OECD Technology Concordance (OTC): Patents by Industry of Manufacture and Sector of Use. OECD Science, Technology and Industry Working Papers, 2002/05. Paris: OECD Publishing. https://doi.org/10.1787/521138670407
- Labaj, M., & Majzlíková, E. (2023). L-M Compilation of Employment Data for FIGARO 2022 Database. Mendeley Data, V1. https://doi.org/10.17632/gzp7rh25g7.1
- Lybbert, T.J., & Zolas, N.J. (2014). Getting patents and economic data to speak to each other: An 'Algorithmic Links with Probabilities' approach for joint analyses of patenting and economic activity. Research Policy, 43(3), 530-542. https://doi.org/10.1016/j.respol.2013.09.001
- OECD (2009). OECD Patent Statistics Manual. Paris: OECD Publishing. ISBN 978-92-64-05412-7.
- World Intellectual Property Organization (WIPO) (2025a). PATENTSCOPE: WIPO's global patent search system. Available at: https://www.wipo.int/en/web/patentscope
- World Intellectual Property Organization (WIPO) (2025b). PATENTSCOPE Artificial Intelligence Index. Available at: https://www.wipo.int/en/web/technology-trends/artificial_intelligence/patentscope
- Trefler, D., & Zhu, S. C. (2010). The structure of factor content predictions. *Journal of International Economics*, 82(2), 195-207.
- Trefler, D. (1995). The Case of the Missing Trade and Other Mysteries. *American Economic Review*, 85(5), 1029-1046.
- Leamer, E. E. (1980). The Leontief Paradox, Reconsidered. *Journal of Political Economy*, 88(3), 495-503.
- Vanek, J. (1968). The Factor Proportions Theory: The N-Factor Case. Kyklos, 21(4), 749-756.
- Schankerman, M., & Pakes, A. (1986). Estimates of the Value of Patent Rights in European Countries During the Post-1950 Period. The Economic Journal, 96(384), 1052-1076.

## Citation

If you use this code or data in your research, please cite:

```
Menghrajani, N. (2025). Comparative Advantage in AI: Positioning the EU amongst its trade partners. [Master's Thesis, TU Delft].
```

## Contact

For questions or access requests prior to publication:

- Nikhil Menghrajani: [nmenghrajani@tudelft.nl](mailto:nmenghrajani@tudelft.nl)
- Roman Stöllinger: [rstollinger@tudelft.nl](mailto:rstollinger@tudelft.nl)

## License

MIT License - see LICENSE file for details.

## Acknowledgments

This research uses data from Eurostat FIGARO, OECD, WIPO, World Bank, Penn World Tables, and various national statistical offices. The AI patent identification follows the WIPO PATENTSCOPE AI Index methodology.