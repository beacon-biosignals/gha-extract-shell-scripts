#!/usr/bin/env python3

# Reads shell scripts from `run` steps in GitHub Actions workflows and outputs
# them as files so that tools like `shfmt` or ShellCheck can operate on them.
#
# Arguments:
# - Path to output directory where shell scripts will be written.

import os
import re
import sys

import argparse
from pathlib import Path

import yaml


def list_str(values):
    return values.split(',')


def sanitize(path):
    # Needed filename replacements to satisfy both GHA artifacts and shellcheck.
    replacements = {
        " ": "_",
        "/": "-",
        '"': "",
        "(": "",
        ")": "",
        "&": "",
        "$": "",
        ":": "",
    }
    return path.translate(str.maketrans(replacements))


# Replace any GHA placeholders, e.g. ${{ matrix.version }}.
def sanitize_gha_expression(string):
    return re.sub(r"\${{\s*(.*?)\s*}}", r":\1:", string)


def process_workflow_file(workflow_path: Path, output_dir: Path, ignored_errors=[]):
    with workflow_path.open() as f:
        workflow = yaml.safe_load(f)
    workflow_file = workflow_path.name
    # GHA allows workflow names to be defined as empty (e.g. `name:`)
    workflow_name = workflow.get("name") or workflow_path.stem
    workflow_default_shell = workflow.get("defaults", {}).get("run", {}).get("shell")
    workflow_env = workflow.get("env", {})
    count = 0
    print(f"Processing {workflow_path} ({workflow_name})")
    for job_key, job in workflow.get("jobs", {}).items():
        # GHA allows job names to be defined as empty (e.g. `name:`)
        job_name = job.get("name") or job_key
        job_default_shell = (
            job.get("defaults", {}).get("run", {}).get("shell", workflow_default_shell)
        )
        job_env = workflow_env | job.get("env", {})
        for i, step in enumerate(job.get("steps", [])):
            run = step.get("run")
            if not run:
                continue
            run = sanitize_gha_expression(run)
            shell = step.get("shell", job_default_shell)
            if shell and shell not in ["bash", "sh"]:
                print(f"Skipping command with unknown shell '{shell}'")
                continue
            env = job_env | step.get("env", {})
            # GHA allows step names to be defined as empty (e.g. `name:`)
            step_name = sanitize(step.get("name") or str(i + 1))
            script_path = (
                output_dir / workflow_file / f"job={sanitize(job_name)}" /
                f"step={sanitize(step_name)}.sh"
            )
            script_path.parent.mkdir(parents=True, exist_ok=True)
            with script_path.open("w") as f:
                # Default shell is bash.
                f.write(f"#!/usr/bin/env {shell or 'bash'}\n")
                # Ignore failure with GitHub expression variables such as:
                # - SC2050: `[[ "${{ github.ref }}" == "refs/heads/main" ]]`
                if ignored_errors:
                    f.write(f"# shellcheck disable={','.join(ignored_errors)}\n")
                    # Add a no-op command to ensure that additional shellcheck
                    # disable directives aren't applied globally
                    # https://github.com/koalaman/shellcheck/issues/657#issuecomment-213038218
                    f.write("true\n")
                # Whether or not it was explicitly set determines the arguments.
                # https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idstepsshell
                if not shell or shell == "sh":
                    f.write("set -e\n")
                elif shell == "bash":
                    f.write("set -eo pipefail\n")
                for k, v in env.items():
                    f.write("# shellcheck disable=SC2016,SC2034\n")
                    v = sanitize_gha_expression(str(v)).replace("'", "'\\''")
                    f.write(f"{k}='{v}'\n")
                f.write("# ---\n")
                f.write(run)
                if not run.endswith("\n"):
                    f.write("\n")
            count += 1
    print(f"Produced {count} files")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--disable", type=list_str)
    args = parser.parse_args()

    print(f"Outputting scripts to {args.output_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for file in os.listdir(args.input_dir):
        if file.endswith(".yaml") or file.endswith(".yml"):
            process_workflow_file(
                args.input_dir / file, args.output_dir, args.disable
            )
