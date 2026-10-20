# Surge filtered module

Source: https://raw.githubusercontent.com/fmz200/wool_scripts/main/Surge/module/blockAds.module

Filter: `music\.126` in `[URL Rewrite]` only. `[Rule]` and `[MITM]` remain unchanged; a matching `[Script]` entry causes a safe failure for manual review.

This is a conservative approximation of KOP-XIAO `out` behavior, not a byte-for-byte implementation of its parser.

## Install
1. Upload these files into a public GitHub repository (preserve `.github/workflows/update.yml`).
2. Enable Actions write permissions in Settings → Actions → General → Workflow permissions, if needed.
3. Actions → Update filtered Surge module → Run workflow.
4. Review `filter-report.json` and the generated `blockAds-filtered.sgmodule` before enabling it.
5. Subscribe in Surge using `https://raw.githubusercontent.com/USER/REPO/main/blockAds-filtered.sgmodule` (replace USER/REPO/branch).
6. Disable the original module to avoid duplicate rules.

## Local dry run
`python filter_surge.py --input blockAds.module --dry-run`

The workflow fails and leaves the last committed output intact if download/validation fails. Scheduled GitHub Actions can be delayed or disabled after inactivity.
