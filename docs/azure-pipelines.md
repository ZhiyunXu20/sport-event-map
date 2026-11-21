# CI/CD with Azure Pipelines

[`azure-pipelines.yml`](../azure-pipelines.yml) runs four stages:

| Stage | What it does | Fails when |
|---|---|---|
| **Validate** | Runs `tools/validate_races.py` on the sample data, runs the publish filter and validates its output, checks every JSON file parses, and syntax-checks `race-map.js` | a race is missing a required field, has an impossible date or coordinate, uses a sport/category with no text in `i18n.json`, points to an area that is not in `assets/geo/`, or has a non-http link |
| **Test** | Runs `pytest` on the data tools and publishes test results and coverage to the run | a unit test fails |
| **Build** | Copies only the files the site needs into a `site` artifact, stamped with the commit | |
| **Deploy** | Uploads the artifact to Azure Static Web Apps, through the `production` environment | runs only on `main`, never for pull requests, and only when you turn it on |

Pull requests to `main` run the first three stages. With a branch policy (or GitHub branch protection that requires this check), a PR with bad data cannot be merged.

## Run the checks locally

```sh
python3 -I tools/validate_races.py examples/races.sample.json   # or your own data/races.json
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

## One-time setup

1. **Organisation and project.** Sign in at <https://dev.azure.com> with a Microsoft account, create an organisation, then a project (Public, so the runs can be linked from a CV).
2. **Connect GitHub.** In the project, go to *Pipelines → New pipeline → GitHub*, authorise, pick this repository and approve the *Azure Pipelines* GitHub App for it. Choose *Existing Azure Pipelines YAML file* and select `/azure-pipelines.yml`.
3. **An agent to run on.** A new organisation has no free Microsoft-hosted parallel job until you ask for one: submit the free-grant request linked from Microsoft's "Configure and pay for parallel jobs" page (it takes a few working days). Until then, register your own machine as a self-hosted agent (*Project settings → Agent pools → Default → New agent*, follow the steps for your OS) and run the pipeline with **Agent = selfhosted**. The machine needs `python3` and `node`.
4. **Status check on GitHub (optional).** In GitHub *Settings → Branches*, add a rule for `main` that requires the Azure Pipelines check to pass.

## Turning on Deploy (optional)

1. Create an Azure account and a **Static Web App** on the Free plan, with *Deployment source: Other*.
2. Copy its deployment token (*Manage deployment token*).
3. In the pipeline, *Edit → Variables*: add `SWA_DEPLOYMENT_TOKEN` (tick *Keep this value secret*) and `DEPLOY_ENABLED` = `true`.
4. In *Pipelines → Environments → production*, add an *Approvals* check if you want to approve each release.

The Deploy stage always uses a Microsoft-hosted Ubuntu agent, because the Static Web Apps task needs Docker. Without the steps above the pipeline is CI only, and the public demo keeps running on GitHub Pages.

## Badge

After the first run, *Pipelines → (this pipeline) → … → Status badge* gives Markdown you can paste at the top of the README.
