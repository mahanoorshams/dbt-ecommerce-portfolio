> ⚠️ **AI transparency:** I used Claude as a pair analyst throughout this project. Claude helped design the experiment, write the dbt models, structure the statistical analysis, and build the Power BI dashboard programmatically. The analytical decisions, interpretation of results, and all the problem-solving described below are my own.

---

# A/B Test: Checkout Free Shipping Banner

**Can showing customers a free shipping threshold at checkout increase average order value?**

This project designs, simulates, and analyses a controlled experiment on the `thelook_ecommerce` BigQuery dataset. The banner treatment is simulated using a deterministic hash of `user_id` rather than live traffic, which is the standard approach for portfolio experimentation on static datasets.

---

## The Result

**Inconclusive. The banner cannot be recommended for rollout based on this test.**

Neither the conversion rate lift (+0.9 percentage points, p = 0.82) nor the AOV difference (negative £0.49, p = 0.96) reached statistical significance at alpha = 0.05. Both results are well within the range of random noise.

This is not a verdict on whether the banner works. It is a verdict on whether this test had enough statistical power to detect an effect. It did not. The experiment captured 463 total orders against a required sample of 14,988, giving it roughly 3% statistical power rather than the target 80%.

The more interesting finding came from the power calculation itself: at this dataset's traffic volume of around 12 completed orders per day, detecting a 5% AOV lift would require over 1,200 days of live testing. That is the real result of this project, and it is documented transparently rather than buried.

---

## What I Built

The project spans four layers:

**Experiment design document** written before any code was run. It includes the hypothesis, primary metric (AOV), guardrail metric (return rate), a power calculation using real baseline figures from BigQuery, and an honest assessment of test feasibility. The design doc is committed to the repo as `experiment_design.md`.

**Two dbt models** in BigQuery that simulate the experiment. `stg_experiment_assignments` assigns every user to control or treatment using a deterministic FARM_FINGERPRINT hash of their user_id. `fct_experiment_results` joins those assignments to orders placed during a defined four-week test window, producing 463 rows across the two variants. Both models are fully tested with 13 dbt tests passing.

**Two Python notebooks** for the analysis. The EDA notebook explores data quality, variant balance (50.8 vs 49.2, essentially perfect), and the raw metric distributions. The statistical analysis notebook runs a two-proportion z-test on conversion rate and a Welch t-test on AOV, calculates 95% confidence intervals for both, checks the guardrail metric, and produces a written product recommendation.

**A Power BI dashboard** built programmatically by writing PBIR JSON files directly into the PBIP project structure using a Node.js script. The dashboard shows KPI cards for each variant, comparison bar charts, and the full go/no-go verdict as a text panel.

---

## Stack

BigQuery · dbt Core · Python (pandas, scipy, statsmodels, matplotlib) · Power BI Desktop (PBIR format) · Node.js (dashboard build script) · GitHub

---

## Baseline Figures

All figures below were calculated from the `thelook_ecommerce` source data before the test window opened.

| Metric | Value |
|---|---|
| Baseline AOV | £86.03 |
| Standard deviation of order value | £93.98 |
| Baseline return rate | 28.6% |
| Average daily completed orders | 12.39 |
| Required sample per variant (80% power, 5% MDE) | 7,494 |
| Estimated test duration at this traffic volume | 1,210 days |

The standard deviation being larger than the mean is worth noting. Order values in fashion retail are highly right-skewed, with a small number of large orders pulling the average up. This inflates the required sample size considerably.

---

## Problems I Hit and How I Fixed Them

**The power calculation produced an impossible test duration.**
Running the sample size formula with real baseline figures gave 1,210 days, not the roughly 30 days I expected. My first instinct was to check whether I had made a calculation error. I had not. The standard deviation of order values ($93.98) is larger than the mean ($86.03), which means the coefficient of variation is above 1, and detecting a 5% lift on a metric that variable requires an enormous sample. The fix was to document this finding honestly in the experiment design document and frame the simulation approach as the deliberate response to a real constraint rather than a workaround.

**The dbt mart model failed on the first run with an `Unrecognized name: id` error.**
The `fct_experiment_results` model referenced `id as order_id` in the orders CTE, but the `thelook_ecommerce.orders` table actually stores the primary key as `order_id` directly. A five-second look at the source schema confirmed the issue. The fix was a single-line edit: remove the alias and reference `order_id` directly.

**FARM_FINGERPRINT replaced MD5 in the assignment model.**
The original experiment design specified an MD5 hash of `user_id` for assignment. In BigQuery Standard SQL, `MD5()` returns BYTES rather than a string, which cannot be used with `MOD()` directly. FARM_FINGERPRINT returns INT64 and is the BigQuery-native alternative for deterministic hashing. The experiment design document was updated to reflect this change and explain the reasoning.

**Two Python versions installed on the same machine caused a `ModuleNotFoundError`.**
When running the EDA notebook, Python threw `No module named 'matplotlib'` even though it had just been installed. The issue was that Python 3.14 (a very recent version with limited package support) was being picked up by the `python` command, while all the data packages were installed under Python 3.12. Uninstalling Python 3.14 and restarting resolved it cleanly.

**The Power BI dashboard visual schema version was wrong.**
The first version of the build script used visual container schema version `5.5.0`, which is too recent for the installed Desktop version. Power BI rejected all 12 visuals with a schema version error. The fix was to read an existing `visual.json` from the NHS RTT project (which uses the same Desktop installation) to discover that the correct version is `2.10.0`, then rewrite the script with that version. The textbox format also turned out to be completely different from what the script had written, requiring a second rewrite before the visuals loaded correctly.

---

## What I Would Do Differently

Run the power calculation before writing any code. I designed the experiment, built the dbt models, and started the Python analysis before I had confirmed the test was feasible at this traffic volume. The 1,210-day finding was a late-stage discovery when it should have been the first thing checked. In a real product environment, running the numbers on traffic and required sample size before any engineering work is non-negotiable.

On a real production dataset with thousands of daily orders, this test would be straightforward. The design, the models, the analysis, and the dashboard are all production-ready. The only thing that would change is swapping the static simulation window for live experiment data.

---

## Run It Yourself

**Prerequisites:** Python 3.12, dbt BigQuery adapter, a Google Cloud project with BigQuery enabled.

```bash
gcloud auth application-default login
```

**Run the dbt models:**
```bash
dbt run --select stg_experiment_assignments fct_experiment_results
dbt test --select stg_experiment_assignments fct_experiment_results
```

**Run the analysis notebooks:**
```bash
pip install -r notebooks/requirements.txt
jupyter lab
```

Open `notebooks/02_exploratory_analysis.ipynb` followed by `notebooks/03_statistical_analysis.ipynb`.

**Rebuild the Power BI dashboard:**
```bash
node documents/ab_testing/build-ab-test-dashboard.js
```
Open `documents/ab_testing/ab-test-dashboard.pbip` in Power BI Desktop.

---

**Built by [Mahanoor Shams](https://github.com/mayasyed)** · [LinkedIn](https://www.linkedin.com/in/mahanoor-shams)
