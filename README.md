# ISM group website

Website of the ISM group at Nazarbayev University. It is being rebuilt as a
static, highly visual site driven by real sky data; see `PLAN.md` for the
current status. The earlier Go and PostgreSQL site is kept at the git tag
`legacy-go-site`.

## Sky renders

`scripts/render_lmc.py` turns public survey data (Planck 353 GHz, GASKAP-HI
with Parkes, MAGMA CO) into aligned web images of the whole sky, the LMC and
other regions the group studies. It reads the LMC workspace's shared data:

    LMC_DATA=~/Projects/LMC/lmc-data python3 scripts/render_lmc.py
    LMC_DATA=~/Projects/LMC/lmc-data python3 scripts/render_lmc.py --regions

Outputs go to `assets/lmc/` (not tracked).
