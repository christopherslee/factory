"""Behavior tests for the work skill: one Steps section for each next_action of the CLI."""
import importlib.machinery
import importlib.util
import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / "skills"


def load_cli():
    loader = importlib.machinery.SourceFileLoader("factory_cli", str(REPO / "bin" / "factory"))
    spec = importlib.util.spec_from_loader("factory_cli", loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["factory_cli"] = mod  # dataclasses look the module up here
    loader.exec_module(mod)
    return mod


def read_skill(name):
    return (SKILLS / name / "SKILL.md").read_text()


def cli_actions():
    """Each next_action value that the CLI can print."""
    cli = load_cli()
    verified = [cli.Event("agent", "advance", "dev", "verify"), cli.Event("human", "verified")]
    actions = {cli.next_action(stage, flags, events)
               for stage in cli.STAGE
               for flags in ([], ["rework"], ["claimed"], ["blocked"])
               for events in ([], verified)}
    actions.discard(None)
    return actions


class WorkSkillTest(unittest.TestCase):
    def test_each_next_action_has_a_steps_section(self):
        text = read_skill("work")
        steps = re.search(r"^## Steps\n(.*?)(?=^## |\Z)", text, re.S | re.M).group(1)
        sections = set(re.findall(r"^### (\w+)$", steps, re.M))
        self.assertEqual(cli_actions(), {"design", "develop", "ship", "rework"})
        self.assertEqual(sections, cli_actions())

    def test_each_next_action_is_in_the_action_table(self):
        text = read_skill("work")
        for action in cli_actions():
            self.assertRegex(text, rf"\| `{action}` \|$".replace("$", r"\n"))

    def test_skill_name_is_work(self):
        self.assertRegex(read_skill("work"), r"^---\nname: work\n")

    def test_foreman_skill_runs_work_and_has_no_brief_table(self):
        text = read_skill("foreman")
        self.assertNotIn("| `next_action` | Brief |", text)
        self.assertIn("Run the skill `/work <ID>`. Do only this issue.", text)

    def test_foreman_does_the_work_in_its_own_session(self):
        text = read_skill("foreman")
        self.assertIn("Do the work here. Do not start a different session.", text)
        self.assertNotIn("Start one work session", text)

    def test_only_foreman_and_work_skills_exist(self):
        self.assertEqual(sorted(p.name for p in SKILLS.iterdir() if p.is_dir()), ["foreman", "work"])

    def test_no_fixed_design_or_mockup_path(self):
        text = read_skill("work")
        self.assertNotIn("home repo", text)
        self.assertIsNone(re.search(r"(?<![\w<>/])(docs/designs|mockups/)", text))

    def test_no_step_runs_a_human_command(self):
        text = read_skill("work")
        for cmd in ("go", "approve", "verified", "move", "unblock"):
            self.assertIsNone(re.search(rf"^\s*\d+\. Run `factory {cmd}\b", text, re.M), f"factory {cmd}")


if __name__ == "__main__":
    unittest.main()
