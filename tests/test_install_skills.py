"""Behavior tests for bin/install-skills: run it as a user does, in a temporary git repo."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "bin" / "install-skills"


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})


class InstallSkillsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name).resolve()
        self.main = root / "factory"
        self.target = root / "skills-installed"
        (self.main / "bin").mkdir(parents=True)
        shutil.copy(SCRIPT, self.main / "bin" / "install-skills")
        for name in ("foreman", "work"):
            (self.main / "skills" / name).mkdir(parents=True)
            (self.main / "skills" / name / "SKILL.md").write_text(f"name: {name}\n")
        git(self.main, "init", "-q", "-b", "main")
        git(self.main, "add", ".")
        git(self.main, "commit", "-q", "-m", "init")
        self.worktree = root / "wt"
        git(self.main, "worktree", "add", "-q", "-b", "feature", str(self.worktree))

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, checkout):
        return subprocess.run([str(checkout / "bin" / "install-skills")], capture_output=True, text=True,
                              env={**os.environ, "SKILLS_DIR": str(self.target)})

    def links(self):
        return {p.name: os.readlink(p) for p in self.target.iterdir() if p.is_symlink()}

    def test_links_each_skill_from_the_main_checkout_also_when_run_in_a_worktree(self):
        r = self.run_script(self.worktree)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.links(), {"foreman": f"{self.main}/skills/foreman", "work": f"{self.main}/skills/work"})

    def test_second_run_gives_the_same_links(self):
        self.run_script(self.main)
        first = self.links()
        self.assertEqual(self.run_script(self.main).returncode, 0)
        self.assertEqual(self.links(), first)

    def test_removes_a_link_to_a_deleted_skill_and_keeps_other_entries(self):
        self.target.mkdir()
        (self.target / "other").mkdir()
        os.symlink(f"{self.main}/skills/design", self.target / "design")
        self.run_script(self.main)
        self.assertEqual(set(self.links()), {"foreman", "work"})
        self.assertTrue((self.target / "other").is_dir())

    def test_refuses_when_the_main_checkout_has_uncommitted_changes(self):
        (self.main / "skills" / "work" / "SKILL.md").write_text("changed\n")
        r = self.run_script(self.main)
        self.assertEqual(r.returncode, 1)
        self.assertIn("uncommitted changes", r.stderr)
        self.assertFalse(self.target.exists())

    def test_refuses_when_the_main_checkout_is_not_on_main(self):
        git(self.main, "switch", "-q", "-c", "other")
        r = self.run_script(self.main)
        self.assertEqual(r.returncode, 1)
        self.assertIn("not main", r.stderr)


if __name__ == "__main__":
    unittest.main()
