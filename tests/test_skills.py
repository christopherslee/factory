"""Behavior tests for the stage skills: one skill for each next_action of the CLI, with equal common blocks."""
import importlib.machinery
import importlib.util
import itertools
import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / "skills"
STAGE_SKILLS = ["design", "develop", "ship", "rework"]
COMMON = ["Start", "Folders", "Rules", "End"]


def load_cli():
    loader = importlib.machinery.SourceFileLoader("factory_cli", str(REPO / "bin" / "factory"))
    spec = importlib.util.spec_from_loader("factory_cli", loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["factory_cli"] = mod  # dataclasses look the module up here
    loader.exec_module(mod)
    return mod


def read_skill(name):
    return (SKILLS / name / "SKILL.md").read_text()


def front_matter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    return dict(line.split(": ", 1) for line in m.group(1).splitlines())


def section(text, title):
    m = re.search(rf"^## {title}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1) if m else None


class StageSkillsTest(unittest.TestCase):
    def test_each_next_action_has_a_skill_with_that_name(self):
        cli = load_cli()
        verified = [cli.Event("agent", "advance", "dev", "verify"), cli.Event("human", "verified")]
        actions = set()
        for stage in cli.STAGE:
            for flags in ([], ["rework"], ["claimed"], ["blocked"]):
                for events in ([], verified):
                    actions.add(cli.next_action(stage, flags, events))
        actions.discard(None)
        self.assertEqual(actions, {"design", "develop", "ship", "rework"})
        for action in actions:
            self.assertEqual(front_matter(read_skill(action))["name"], action)

    def test_common_blocks_are_the_same_text_in_the_four_skills(self):
        for title in COMMON:
            texts = {name: section(read_skill(name), title) for name in STAGE_SKILLS}
            self.assertNotIn(None, texts.values(), f"## {title} is missing in {texts}")
            for a, b in itertools.combinations(STAGE_SKILLS, 2):
                self.assertEqual(texts[a], texts[b], f"## {title} differs between {a} and {b}")

    def test_foreman_skill_has_no_brief_table(self):
        text = read_skill("foreman")
        self.assertNotIn("| `next_action` | Brief |", text)
        self.assertIn("Run the skill `/<next_action> <ID>`", text)

    def test_no_stage_skill_has_a_fixed_design_or_mockup_path(self):
        for name in STAGE_SKILLS:
            text = read_skill(name)
            self.assertNotIn("home repo", text, name)
            self.assertIsNone(re.search(r"(?<![\w<>/])(docs/designs|mockups/)", text), name)

    def test_no_stage_skill_permits_a_human_command(self):
        for name in STAGE_SKILLS:
            text = read_skill(name)
            for cmd in ("go", "approve", "verified", "move", "unblock"):
                self.assertIsNone(re.search(rf"^\s*\d+\. Run `factory {cmd}\b", text, re.M), f"{name}: factory {cmd}")


if __name__ == "__main__":
    unittest.main()
