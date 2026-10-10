# Data Sources and Data Quality

## Development defaults
The committed `data/sample/` files are synthetic and intended only for reproducible software tests. They are not actual mutual fund or index history.

## Indian mutual fund NAV
MFAPI.in exposes mutual fund scheme metadata and historical NAV data. The helper `scripts/fetch_mfapi_nav.py` queries the public API by scheme code and writes normalized rows. Verify the scheme identifier, scheme name/category, date coverage, and provider terms before project use. Consult the provider's own API documentation: https://www.mfapi.in/

For official scheme NAV data and fund disclosures, also consult AMFI India: https://www.amfiindia.com/

## Benchmarks
Use a benchmark appropriate to the fund's stated investment mandate. NSE Indices publishes information about its indices: https://www.niftyindices.com/ . Prefer total-return index data where available because price-only indices do not include reinvested distributions. Verify data access, publication rules, and licensing before redistributing any downloaded series.

## Data quality checklist
- Dates parse correctly and observations are sorted.
- Scheme code and date uniquely identify a NAV record.
- Benchmark name and date uniquely identify an index record.
- NAV and index levels are positive and numeric.
- Time coverage is sufficiently long and overlapping across funds and benchmark.
- Missing data is investigated; returns are not silently forward-filled.
- A fund category is paired with a suitable benchmark.
- Dividends/distributions, direct vs regular plan, growth vs IDCW plan, and survivorship bias are considered.
- Risk-free rate, return periodicity and annualization conventions are documented.

## Output interpretation
No analytic estimate should be presented as an investment guarantee. CAPM, PCA, portfolio optimization, and stress testing are sensitive to sample selection and assumptions.
