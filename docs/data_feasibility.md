# Data feasibility check (due Sat Nov 7, about 2 hours)

Goal: confirm that the data for the rescoped model (D12 in `PROJECT_STATE.md`) exists, for 2019 and 2022, at a usable time step and under a usable licence. Do not assume it is sufficient until you have opened the files.

Raw downloads go in `data/` (gitignored). **Never commit raw data.**

## Steps

1. Download the éCO2mix national consolidated and definitive data for 2019 and 2022: <https://odre.opendatasoft.com/explore/dataset/eco2mix-national-cons-def/> (dataset page on data.gouv.fr: <https://www.data.gouv.fr/datasets/donnees-eco2mix-nationales-consolidees-et-definitives>).
2. Load each year in pandas. Print the column names, the first rows, the time step, and the number of rows per year.
3. Fill rows 1–6 of the table below from what you actually see.
4. Spend at most 20 minutes each on rows 7–9. If you find nothing, write "not found" and move on: that is a finding, not a failure.

What Browser Claude read on the dataset page (2026-11-01, not yet confirmed in the files): Licence Ouverte / Open Licence 2.0; 30-minute step for consumption, production by source and exchanges; coverage 2012–2024. The page does not list the fuel categories by name.

## Table

"Exogenous?" asks whether the series can be an **input** to the model. A series the model is supposed to produce (for example, gas generation) cannot also be an input.

| # | Variable | Source | Column name and unit (as seen) | Time step (as seen) | 2019 present? | 2022 present? | Licence | Exogenous? | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Demand (consumption) | éCO2mix | | | | | | Yes | |
| 2 | Wind generation | éCO2mix | | | | | | Yes (fixed profile) | |
| 3 | Solar generation | éCO2mix | | | | | | Yes (fixed profile) | |
| 4 | Hydro generation | éCO2mix | | | | | | Yes (fixed profile; limitation) | |
| 5 | Net imports / exchanges | éCO2mix | | | | | | Yes (fixed profile; limitation) | |
| 6 | Nuclear generation | éCO2mix | | | | | | Only as a proxy for availability | |
| 7 | Nuclear availability (capacity) | ENTSO-E unavailability data, or RTE/EDF | | | | | | Yes | |
| 8 | Gas price | to find | | | | | | Yes | |
| 9 | Carbon (EU ETS) price | to find | | | | | | Yes | |
| 10 | Technology costs and efficiencies | RTE / IEA / JRC publications | | n/a | | | | Yes | goes to `ASSUMPTIONS.md` |

Verdict: **sufficient**, **insufficient**, or **needs a workaround** (one line why).

## Questions to answer at the end

- Do the time stamps use UTC or local time? How are daylight-saving changes handled?
- Is 2022 marked as consolidated or definitive?
- Does nuclear generation in 2022 visibly drop in particular months? (This decides whether one load-duration curve per year is enough, or one per season is needed.)
