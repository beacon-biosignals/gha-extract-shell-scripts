# GHA Extract Shell Scripts

Processes the GitHub Action workflows contained within `.github/workflows` and extracts all steps which contain an embedded shell script for the purpose of running linting and formatting. Each workflow step containing a shell script will be written out to a file to make it easy to use existing tooling such as `shellcheck` and `shfmt`.

## Example

```yaml
---
name: Shell
on:
  pull_request:
    paths:
      - "**.sh"
      - ".github/workflows/*"

jobs:
  lint-format:
    name: Lint & Format
    # These permissions are needed to:
    # - Checkout the Git repo (`contents: read`)
    # - Post a comments on PRs: https://github.com/luizm/action-sh-checker#secrets
    permissions:
      contents: read
      pull-requests: write
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Extract workflow shell scripts
        uses: beacon-biosignals/gha-extract-shell-scripts@v1
      - uses: luizm/action-sh-checker@c6edb3de93e904488b413636d96c6a56e3ad671a  # v0.8.0
        env:
          GITHUB_TOKEN: ${{ github.token }}
        with:
          sh_checker_comment: true
```

## Inputs

The `gha-extract-shell-scripts` action supports the following inputs:

| Name                 | Description | Required | Example |
|:---------------------|:------------|:---------|:--------|
| `output-dir`         | Allows the user to specify the name of the directory containing the extracted workflow shell script steps. Defaults to `workflow_scripts`. | No | `workflow_scripts` |
| `shellcheck-disable` | Ignore all the specified errors within the extracted shell scripts. | No | `SC2016,SC2050` |

## Outputs

| Name         | Description | Example |
|:-------------|:------------|:--------|
| `output-dir` | The name of the directory containing the various extracted workflow shell script steps. | `workflow_scripts` |

## Permissions

The following [job permissions](https://docs.github.com/en/actions/using-jobs/assigning-permissions-to-jobs) are required to run this action:

```yaml
permissions: {}
```
