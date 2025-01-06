import inspect
from pathlib import Path
import os
import shutil
import sys
import textwrap
import unittest

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(TEST_DIR))

from gha_extract_shell_scripts import process_workflow_file

def clean(string):
    string = textwrap.dedent(string).rstrip()
    return [l + "\n" for l in string.split("\n")]


class TestReferenceWorkflows(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def tearDown(self):
        shutil.rmtree("workflow_scripts")

    def test_github_actions_demo(self):
        output_dir = Path("workflow_scripts")
        process_workflow_file(Path(f"{TEST_DIR}/github-actions-demo.yaml"), output_dir)
        self.assertTrue(os.path.isdir(f"{output_dir}"))
        self.assertTrue(os.path.isdir(f"{output_dir}/github-actions-demo.yaml"))
        self.assertTrue(os.path.isdir(f"{output_dir}/github-actions-demo.yaml/job=Explore-GitHub-Actions"))

        self.assertTrue(os.path.isfile(f"{output_dir}/github-actions-demo.yaml/job=Explore-GitHub-Actions/step=1.sh"))
        with open(f"{output_dir}/github-actions-demo.yaml/job=Explore-GitHub-Actions/step=1.sh") as f:
            expected = """\
                #!/usr/bin/env bash
                set -e
                # ---
                echo "🎉 The job was automatically triggered by a :github.event_name: event."
                """
            self.assertListEqual(list(f), clean(expected))

        self.assertFalse(os.path.isfile(f"{output_dir}/github-actions-demo.yaml/job=Explore-GitHub-Actions/step=4.sh"))
        self.assertTrue(os.path.isfile(f"{output_dir}/github-actions-demo.yaml/job=Explore-GitHub-Actions/step=List_files_in_the_repository.sh"))
        with open(f"{output_dir}/github-actions-demo.yaml/job=Explore-GitHub-Actions/step=List_files_in_the_repository.sh") as f:
            expected = """\
                #!/usr/bin/env bash
                set -e
                # ---
                ls :github.workspace:
                """
            self.assertListEqual(list(f), clean(expected))

    def test_nested_env(self):
        output_dir = Path("workflow_scripts")
        process_workflow_file(Path(f"{TEST_DIR}/nested-env.yaml"), output_dir)
        self.assertTrue(os.path.isdir(f"{output_dir}"))
        self.assertTrue(os.path.isdir(f"{output_dir}/nested-env.yaml"))
        self.assertTrue(os.path.isdir(f"{output_dir}/nested-env.yaml/job=test"))

        self.assertTrue(os.path.isfile(f"{output_dir}/nested-env.yaml/job=test/step=Print_variables.sh"))
        with open(f"{output_dir}/nested-env.yaml/job=test/step=Print_variables.sh") as f:
            expected = """\
                #!/usr/bin/env bash
                set -e
                # shellcheck disable=SC2016,SC2034
                foo='1'
                # shellcheck disable=SC2016,SC2034
                bar='2'
                # shellcheck disable=SC2016,SC2034
                baz='3'
                # ---
                echo -e "foo=$foo\\nbar=$bar\\nbaz=$baz"
                """
            self.assertListEqual(list(f), clean(expected))


if __name__ == '__main__':
    unittest.main()
