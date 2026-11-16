"""Behavior tests: run bin/factory as a user does, against a fake GitHub (FACTORY_FAKE)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

FACTORY = Path(__file__).resolve().parents[1] / "bin" / "factory"


class FactoryCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.fake = self.root / "github.json"
        self.make_foreman("zz", "acme/zz-home", wip='design = 1\ndev = 1')

    def tearDown(self):
        self.tmp.cleanup()

    def make_foreman(self, name, github, folder=None, wip="", register=True, prefix=None):
        d = self.root / (folder or f"{name}-home")
        d.mkdir(exist_ok=True)
        (d / "foreman.toml").write_text(
            f'name = "{name}"\n' + (f'prefix = "{prefix}"\n' if prefix else "") +
            f'github = "{github}"\n[[repos]]\nname = "app"\npath = "../app"\n[wip]\n{wip}\n')
        if register:
            self.factory("register", str(d))
        return d

    def factory(self, *args, cwd=None, ok=True):
        env = {**os.environ, "FACTORY_REGISTRY": str(self.root / "foremen.toml"), "FACTORY_FAKE": str(self.fake)}
        r = subprocess.run([str(FACTORY), *args], capture_output=True, text=True, env=env, cwd=cwd or self.root)
        if ok is True:
            self.assertEqual(r.returncode, 0, f"factory {' '.join(args)}\n{r.stderr}")
        elif ok is False:
            self.assertEqual(r.returncode, 1, f"expected refusal: factory {' '.join(args)}\n{r.stdout}{r.stderr}")
        return (r.stdout + r.stderr).strip()

    def db(self):
        return json.loads(self.fake.read_text())["acme/zz-home"]["issues"]

    def stage(self, n):
        return self.db()[str(n)]["stage"]


class TestLifecycle(FactoryCase):
    def test_full_path_alternates_human_and_agent(self):
        self.assertEqual(self.factory("new", "Export yardages", "--foreman", "zz"), "ZZ-1: created in Backlog")
        self.assertEqual(self.factory("advance", "ZZ-1", ok=False),
                         "refused: Backlog → In Design is a human move (`factory go`)")
        self.assertEqual(self.factory("go", "zz 1"), "ZZ-1: Backlog → In Design")
        self.assertEqual(self.factory("advance", "ZZ-1"), "ZZ-1: In Design → Ready for Dev")
        self.assertEqual(self.factory("advance", "ZZ-1", ok=False),
                         "refused: Ready for Dev → In Dev is a human move (`factory approve`)")
        self.assertEqual(self.factory("approve", "zz#1"), "ZZ-1: Ready for Dev → In Dev")
        self.assertEqual(self.factory("advance", "ZZ-1"), "ZZ-1: In Dev → Verify")
        self.assertEqual(self.factory("advance", "ZZ-1", ok=False),
                         "refused: the last move was an agent move; a human event must come first")
        self.assertEqual(self.factory("verified", "ZZ-1"),
                         "ZZ-1: verified; the agent can now merge, test and close")
        self.assertEqual(self.factory("advance", "ZZ-1"), "ZZ-1: Verify → Done")
        self.assertEqual(self.stage(1), "done")
        self.assertEqual(self.db()["1"]["state"], "closed")

    def test_human_event_without_verified_does_not_permit_ship(self):
        self.factory("new", "X", "--foreman", "zz")
        self.factory("go", "ZZ-1")
        self.factory("advance", "ZZ-1")
        self.factory("approve", "ZZ-1")
        self.factory("advance", "ZZ-1")
        self.factory("rework", "ZZ-1", "Fix the label")
        self.factory("reworked", "ZZ-1")
        self.assertEqual(self.factory("advance", "ZZ-1", ok=False),
                         "refused: Verify → Done needs the human directive `verified`")

    def test_human_move_back_permits_a_new_agent_move(self):
        self.factory("new", "X", "--foreman", "zz")
        self.factory("go", "ZZ-1")
        self.factory("advance", "ZZ-1")
        self.factory("approve", "ZZ-1")
        self.factory("advance", "ZZ-1")
        self.assertEqual(self.factory("move", "ZZ-1", "dev", "--note", "Button is wrong"),
                         "ZZ-1: Verify → In Dev")
        self.assertEqual(self.factory("advance", "ZZ-1"), "ZZ-1: In Dev → Verify")

    def test_old_verified_does_not_carry_over_after_rework(self):
        self.factory("new", "X", "--foreman", "zz")
        for cmd in (["go"], ["advance"], ["approve"], ["advance"], ["verified"]):
            self.factory(*cmd, "ZZ-1")
        self.factory("move", "ZZ-1", "dev")
        self.factory("advance", "ZZ-1")
        self.assertEqual(self.factory("advance", "ZZ-1", ok=False),
                         "refused: the last move was an agent move; a human event must come first")

    def test_stage_change_outside_factory_counts_as_human_event(self):
        # The owner drags the card on the board: Ready for Dev → In Dev is the same as `approve`.
        self.factory("new", "X", "--foreman", "zz")
        self.factory("go", "ZZ-1")
        self.factory("advance", "ZZ-1")
        self.assertEqual(self.factory("advance", "ZZ-1", ok=False),
                         "refused: Ready for Dev → In Dev is a human move (`factory approve`)")
        db = json.loads(self.fake.read_text())
        db["acme/zz-home"]["issues"]["1"]["stage"] = "dev"
        self.fake.write_text(json.dumps(db))
        self.assertEqual(self.factory("advance", "ZZ-1"), "ZZ-1: In Dev → Verify")
        self.assertEqual(self.factory("advance", "ZZ-1", ok=False),
                         "refused: the last move was an agent move; a human event must come first")

    def test_drag_from_backlog_is_the_same_as_go(self):
        self.factory("new", "X", "--foreman", "zz")
        db = json.loads(self.fake.read_text())
        db["acme/zz-home"]["issues"]["1"]["stage"] = "design"
        self.fake.write_text(json.dumps(db))
        self.assertEqual(self.factory("advance", "ZZ-1"), "ZZ-1: In Design → Ready for Dev")

    def test_directive_in_wrong_stage_is_refused(self):
        self.factory("new", "X", "--foreman", "zz")
        self.assertEqual(self.factory("approve", "ZZ-1", ok=False),
                         "refused: ZZ-1 is in Backlog; `approve` needs Ready for Dev")
        self.assertEqual(self.factory("verified", "ZZ-1", ok=False),
                         "refused: ZZ-1 is in Backlog; `verified` needs Verify")

    def test_move_sets_the_stage_and_reopens(self):
        self.factory("new", "X", "--foreman", "zz")
        self.factory("move", "ZZ-1", "done")
        self.assertEqual(self.db()["1"]["state"], "closed")
        self.factory("move", "ZZ-1", "backlog")
        self.assertEqual(self.stage(1), "backlog")
        self.assertEqual(self.db()["1"]["state"], "open")


class TestClaims(FactoryCase):
    def test_claim_is_exclusive_and_idempotent(self):
        self.factory("new", "X", "--foreman", "zz")
        self.assertEqual(self.factory("claim", "ZZ-1", "s1"), "ZZ-1: claimed by s1")
        self.assertEqual(self.factory("claim", "ZZ-1", "s1"), "ZZ-1: already claimed by s1")
        self.assertEqual(self.factory("claim", "ZZ-1", "s2", ok=False), "refused: ZZ-1 is claimed by s1")
        self.assertEqual(self.factory("release", "ZZ-1"), "ZZ-1: released")
        self.assertEqual(self.factory("claim", "ZZ-1", "s2"), "ZZ-1: claimed by s2")

    def test_claim_does_not_count_as_human_event(self):
        self.factory("new", "X", "--foreman", "zz")
        self.factory("go", "ZZ-1")
        self.factory("advance", "ZZ-1")
        self.factory("claim", "ZZ-1", "s1")
        self.factory("release", "ZZ-1")
        self.assertEqual(self.factory("advance", "ZZ-1", ok=False),
                         "refused: Ready for Dev → In Dev is a human move (`factory approve`)")


class TestStatus(FactoryCase):
    def test_status_plans_starts_inside_wip_limits(self):
        for t in ("A", "B", "C", "D"):
            self.factory("new", t, "--foreman", "zz")
        self.factory("go", "ZZ-1")
        self.factory("go", "ZZ-2")
        self.factory("go", "ZZ-3")
        self.factory("advance", "ZZ-3")
        self.factory("approve", "ZZ-3")
        st = json.loads(self.factory("status", "zz", "--json"))
        actions = {i["id"]: i["next_action"] for i in st["issues"]}
        self.assertEqual(actions, {"ZZ-1": "design", "ZZ-2": "design", "ZZ-3": "develop", "ZZ-4": None})
        self.assertEqual(st["start"], ["ZZ-1", "ZZ-3"])

    def test_claimed_issue_uses_wip_and_is_not_restarted(self):
        self.factory("new", "A", "--foreman", "zz")
        self.factory("new", "B", "--foreman", "zz")
        self.factory("go", "ZZ-1")
        self.factory("go", "ZZ-2")
        self.factory("claim", "ZZ-1", "s1")
        st = json.loads(self.factory("status", "zz", "--json"))
        self.assertEqual(st["start"], [])

    def test_verified_issue_gets_ship_action(self):
        self.factory("new", "A", "--foreman", "zz")
        for cmd in ("go", "advance", "approve", "advance"):
            self.factory(cmd, "ZZ-1")
        st = json.loads(self.factory("status", "zz", "--json"))
        self.assertEqual(st["issues"][0]["next_action"], None)
        self.factory("verified", "ZZ-1")
        st = json.loads(self.factory("status", "zz", "--json"))
        self.assertEqual(st["issues"][0]["next_action"], "ship")
        self.assertEqual(st["start"], ["ZZ-1"])

    def test_issue_that_is_not_on_the_board_has_no_stage(self):
        self.factory("new", "A", "--foreman", "zz")
        db = json.loads(self.fake.read_text())
        db["acme/zz-home"]["issues"]["1"]["stage"] = None
        self.fake.write_text(json.dumps(db))
        missing = "ZZ-1 has no stage: it is not on the board; a human must run `factory move ZZ-1 backlog`"
        self.assertEqual(self.factory("audit", "zz", ok=False), f"refused: \n{missing}")
        self.assertEqual(self.factory("advance", "ZZ-1", ok=False), f"refused: {missing}")
        self.assertEqual(self.factory("move", "ZZ-1", "backlog"), "ZZ-1: not on the board → Backlog")
        self.assertEqual(self.factory("audit", "zz"), "no problems")

    def test_audit_finds_an_open_issue_in_done(self):
        # The owner drags the card to Done on the board. That does not close the issue.
        self.factory("new", "A", "--foreman", "zz")
        db = json.loads(self.fake.read_text())
        db["acme/zz-home"]["issues"]["1"]["stage"] = "done"
        self.fake.write_text(json.dumps(db))
        self.assertEqual(self.factory("audit", "zz", ok=False),
                         "refused: \nZZ-1: in Done but the issue is open; a human must close it or move it")

    def test_setup_makes_the_board_once_and_writes_its_number(self):
        toml = self.root / "zz-home" / "foreman.toml"
        self.assertEqual(self.factory("setup", "zz"),
                         "zz: the board and the flag labels are ready (Project 1 made, foreman.toml updated)")
        self.assertEqual(toml.read_text(), 'name = "zz"\ngithub = "acme/zz-home"\n'
                         'project = 1   # the board; `factory setup` wrote this\n'
                         '[[repos]]\nname = "app"\npath = "../app"\n[wip]\ndesign = 1\ndev = 1\n')
        self.assertEqual(self.factory("setup", "zz"), "zz: the board and the flag labels are ready")
        self.assertEqual(toml.read_text().count("project ="), 1)
        repos = json.loads(self.factory("status", "zz", "--json"))["repos"]
        self.assertEqual([r["name"] for r in repos], ["app"])

    def test_setup_finds_the_board_with_the_same_title(self):
        self.factory("setup", "zz")
        d = self.make_foreman("yy", "acme/yy-home")
        (d / "foreman.toml").write_text('name = "yy"\ntitle = "zz"\ngithub = "acme/yy-home"')
        self.assertEqual(self.factory("setup", "yy"),
                         "yy: the board and the flag labels are ready (Project 1 found, foreman.toml updated)")
        self.assertEqual((d / "foreman.toml").read_text(), 'name = "yy"\ntitle = "zz"\ngithub = "acme/yy-home"\n'
                         'project = 1   # the board; `factory setup` wrote this\n')

    def test_project_must_be_a_number(self):
        d = self.root / "zz-home"
        (d / "foreman.toml").write_text('name = "zz"\ngithub = "acme/zz-home"\nproject = "one"\n')
        self.assertEqual(self.factory("status", "zz", ok=None),
                         f"error: {d / 'foreman.toml'}: project must be the number of a GitHub Project, got 'one'")

    def test_real_backend_needs_a_project(self):
        env = {**os.environ, "FACTORY_REGISTRY": str(self.root / "foremen.toml")}
        env.pop("FACTORY_FAKE", None)
        r = subprocess.run([str(FACTORY), "status", "zz"], capture_output=True, text=True, env=env)
        self.assertEqual((r.returncode, r.stderr.strip()), (2, f"error: {self.root / 'zz-home' / 'foreman.toml'}: "
                         "set project to the number of the GitHub Project (the board), "
                         "or run `factory setup` to make the board"))


class TestProjectHome(FactoryCase):
    def write_home(self, line):
        d = self.root / "zz-home"
        (d / "foreman.toml").write_text(f'name = "zz"\ngithub = "acme/zz-home"\n{line}\n')
        return d

    def test_without_home_the_registry_folder_is_the_home(self):
        d = self.root / "zz-home"
        st = json.loads(self.factory("status", "zz", "--json"))
        self.assertEqual((st["root"], st["home"], st["designs"], st["mockups"]),
                         (str(d), str(d), str(d / "docs" / "designs"), str(d / "mockups")))
        self.assertNotIn("project home", self.factory("status", "zz"))

    def test_home_names_a_separate_project_home(self):
        (self.root / "zz-project").mkdir()
        d = self.write_home('home = "../zz-project"')
        st = json.loads(self.factory("status", "zz", "--json"))
        p = self.root / "zz-project"
        self.assertEqual((st["root"], st["home"], st["designs"], st["mockups"]),
                         (str(d), str(p), str(p / "docs" / "designs"), str(p / "mockups")))
        self.assertEqual(self.factory("status", "zz").splitlines()[:2],
                         ["zz (acme/zz-home)", f"project home: {p}"])

    def test_home_must_be_an_existing_folder(self):
        d = self.write_home('home = "../nowhere"')
        self.assertEqual(self.factory("status", "zz", ok=None),
                         f"error: {d / 'foreman.toml'}: home '{self.root / 'nowhere'}' is not a folder")

    def test_home_must_be_a_path(self):
        d = self.write_home("home = 3")
        self.assertEqual(self.factory("status", "zz", ok=None),
                         f"error: {d / 'foreman.toml'}: home must be the path of the project home folder, got 3")


class TestRefs(FactoryCase):
    def test_all_reference_forms_resolve_to_one_id(self):
        self.make_foreman("cc", "acme/cc-home")
        for text in ("CC-42", "cc#42", "cc 42", "Cc-42"):
            self.assertEqual(json.loads(self.factory("resolve", text))["id"], "CC-42", text)

    def test_bare_number_uses_the_foreman_of_the_current_folder(self):
        cc = self.make_foreman("cc", "acme/cc-home")
        (cc / "docs").mkdir()
        self.assertEqual(json.loads(self.factory("resolve", "42", cwd=cc / "docs"))["id"], "CC-42")

    def test_prefix_names_the_issues_and_the_name_stays_for_directives(self):
        ww = self.make_foreman("ww", "acme/ww-home", prefix="widget")
        self.assertEqual(self.factory("new", "X", "--foreman", "ww"), "WIDGET-1: created in Backlog")
        for text in ("WIDGET-1", "widget#1", "widget 1", "ww-1", "ww 1", "WW-1"):
            self.assertEqual(json.loads(self.factory("resolve", text)),
                             {"id": "WIDGET-1", "foreman": "ww", "github": "acme/ww-home", "number": 1}, text)
        self.assertEqual(json.loads(self.factory("resolve", "1", cwd=ww))["id"], "WIDGET-1")
        self.assertEqual(self.factory("go", "ww 1"), "WIDGET-1: Backlog → In Design")
        self.assertIn("WIDGET-1", self.factory("status", "ww"))

    def test_prefix_must_have_the_form_of_a_name(self):
        d = self.make_foreman("ww", "acme/ww-home", prefix="Wid get", register=False)
        self.assertEqual(self.factory("register", str(d), ok=None),
                         f"error: {d / 'foreman.toml'}: prefix 'Wid get' must be 2-8 lowercase letters or digits, "
                         "first a letter")

    def test_prefix_of_one_foreman_must_not_be_the_name_or_prefix_of_another(self):
        self.make_foreman("ww", "acme/ww-home", prefix="zz")
        self.assertEqual(self.factory("resolve", "zz-1", ok=None),
                         "error: 'zz' is the name or prefix of more than one foreman: ww, zz; "
                         "change a prefix in foreman.toml")

    def test_unknown_foreman_is_an_error(self):
        out = self.factory("resolve", "qq-1", ok=None)
        self.assertEqual(out, "error: no foreman named 'qq'; known: zz")

    def test_register_is_idempotent_and_names_are_unique(self):
        zz = self.root / "zz-home"
        self.assertEqual(self.factory("register", str(zz)), f"zz: already registered at {zz.resolve()}")
        self.make_foreman("zz", "acme/other", folder="other-home", register=False)
        self.assertEqual(self.factory("register", str(self.root / "other-home"), ok=False),
                         f"refused: 'zz' is already registered at {zz.resolve()}; use another name or edit "
                         f"{self.root / 'foremen.toml'}")

    def test_registry_file_lists_name_and_folder(self):
        self.make_foreman("cc", "acme/cc-home")
        lines = (self.root / "foremen.toml").read_text().splitlines()[1:]
        self.assertEqual(lines, [f'cc = "{(self.root / "cc-home").resolve()}"',
                                 f'zz = "{(self.root / "zz-home").resolve()}"'])
        self.assertEqual(self.factory("foremen").splitlines()[0].split()[:2], ["cc", "acme/cc-home"])

    def test_unregistered_folder_is_an_error(self):
        qq = self.make_foreman("qq", "acme/qq-home", register=False)
        self.assertEqual(self.factory("resolve", "7", cwd=qq, ok=None),
                         f"error: foreman 'qq' is not registered; run `factory register {qq.resolve()}`")

    def test_registry_and_foreman_toml_must_agree(self):
        zz = self.root / "zz-home"
        (zz / "foreman.toml").write_text('name = "yy"\ngithub = "acme/zz-home"\n')
        self.assertEqual(self.factory("resolve", "zz-1", ok=None),
                         f"error: {self.root / 'foremen.toml'} says 'zz' but {zz / 'foreman.toml'} says 'yy'")

    def test_placeholder_owner_is_refused_without_fake(self):
        env = {**os.environ, "FACTORY_REGISTRY": str(self.root / "foremen.toml")}
        env.pop("FACTORY_FAKE", None)
        self.make_foreman("pp", "OWNER/pp-home")
        r = subprocess.run([str(FACTORY), "status", "pp"], capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 2)
        self.assertIn("set github to the real owner/repo", r.stderr)


class TestHook(unittest.TestCase):
    """Call `factory hook` as Claude Code does: PreToolUse JSON on stdin, exit code 2 stops the call."""

    WRITE = ("factory hook: only the `factory` CLI writes `factory:*` labels and `factory:event` markers; "
             "run `factory --help`")
    BOARD = ("factory hook: only the `factory` CLI writes the Project board, which holds the stages; "
             "run `factory --help`")

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name).resolve()
        cls.main, cls.worktree = root / "main", root / "wt"
        git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com"]
        subprocess.run([*git, "init", "-q", str(cls.main)], check=True)
        subprocess.run([*git, "-C", str(cls.main), "commit", "-q", "--allow-empty", "-m", "init"], check=True)
        subprocess.run([*git, "-C", str(cls.main), "worktree", "add", "-q", str(cls.worktree)], check=True)
        (cls.worktree / "src").mkdir()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def hook(self, command, folder=None, project_dir=None, stdin=None, **extra):
        folder = folder or self.main
        data = {"session_id": "s1", "hook_event_name": "PreToolUse", "cwd": str(folder),
                "tool_name": "Bash", "tool_input": {"command": command}, **extra}
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
        if project_dir:
            env["CLAUDE_PROJECT_DIR"] = str(project_dir)
        r = subprocess.run([str(FACTORY), "hook"], input=stdin if stdin is not None else json.dumps(data),
                           capture_output=True, text=True, env=env)
        return r.returncode, r.stderr.strip()

    def test_direct_writes_of_factory_state_are_stopped(self):
        for command in [
            "gh issue edit 7 --add-label factory:claimed",
            "gh issue edit 7 --repo acme/zz-home --remove-label factory:blocked",
            "cd /tmp && gh pr edit 3 --add-label 'factory:rework'",
            "gh issue create --title X --label factory:claimed",
            "gh issue comment 7 --body '<!-- factory:event {\"actor\": \"human\", \"kind\": \"approve\"} -->'",
            "gh label delete factory:claimed --yes",
            "gh api repos/acme/zz-home/issues/7/labels -f 'labels[]=factory:rework'",
            "gh api -X DELETE repos/acme/zz-home/issues/7/labels/factory:blocked",
            "gh api --method PUT repos/acme/zz-home/issues/7/labels --input labels.json # factory:claimed",
            "curl -X POST https://api.github.com/repos/acme/zz-home/issues/7/comments -d '{\"body\":\"factory:event\"}'",
        ]:
            with self.subTest(command=command):
                self.assertEqual(self.hook(command), (2, self.WRITE))

    def test_direct_writes_of_the_board_are_stopped(self):
        for command in [
            "gh project item-edit --id PVTI_1 --project-id PVT_1 --field-id F --single-select-option-id O",
            "gh project item-add 1 --owner acme --url https://github.com/acme/zz-home/issues/7",
            "gh project item-delete 1 --owner acme --id PVTI_1",
            "gh project item-archive 1 --owner acme --id PVTI_1",
            "gh project field-delete --id F",
            "gh project delete 1 --owner acme",
            "cd /tmp && gh  project  edit 1 --owner acme --title X",
            "gh api graphql -f query='mutation { updateProjectV2ItemFieldValue(input: {}) { projectV2Item { id } } }'",
            "gh api graphql -f query='mutation($p:ID!){ addProjectV2ItemById(input:{projectId:$p}){ item { id } } }'",
        ]:
            with self.subTest(command=command):
                self.assertEqual(self.hook(command), (2, self.BOARD))

    def test_reads_and_factory_commands_pass(self):
        for command in [
            "gh issue list --label factory:blocked",
            "gh issue view 7 --json labels",
            "gh api 'repos/acme/zz-home/issues?labels=factory:blocked' --jq '.[].number'",
            "gh project list --owner acme",
            "gh project view 1 --owner acme",
            "gh project item-list 1 --owner acme --format json",
            "gh project field-list 1 --owner acme",
            "gh api graphql -f query='query { viewer { projectV2(number: 1) { id } } }'",
            "gh api graphql -f query='mutation { addStar(input: {starrableId: \"x\"}) { clientMutationId } }'",
            "gh issue comment 7 --body 'The design is ready.'",
            "gh issue edit 7 --add-label bug",
            "factory advance ZZ-7",
            "factory ready-to-try ZZ-7 abc1234",
            "factory status zz",
            "grep -rn 'factory:event' docs/",
            "git commit -m 'Add the dev stage'",
        ]:
            with self.subTest(command=command):
                self.assertEqual(self.hook(command, folder=self.worktree), (0, ""))

    def test_human_commands_are_stopped_in_a_work_session(self):
        for command, name in [
            ("factory go ZZ-7", "go"),
            ("factory approve zz#7", "approve"),
            ("factory verified ZZ-7", "verified"),
            ("factory move ZZ-7 dev", "move"),
            ("factory rework ZZ-7 'Fix it'", "rework"),
            ("factory unblock ZZ-7", "unblock"),
            ("factory try ZZ-7", "try"),
            ("bin/factory approve ZZ-7", "approve"),
            ("~/.local/bin/factory approve ZZ-7", "approve"),
            ("factory advance ZZ-7 && factory approve ZZ-7", "approve"),
            ("FACTORY_REGISTRY=x factory  approve ZZ-7", "approve"),
        ]:
            with self.subTest(command=command):
                self.assertEqual(self.hook(command, folder=self.worktree), (
                    2, f"factory hook: `factory {name}` is a human command; a work session cannot run it. "
                       "Stop and report to the owner."))

    def test_work_session_is_found_from_a_subfolder_of_the_worktree(self):
        self.assertEqual(self.hook("factory approve ZZ-7", folder=self.worktree / "src")[0], 2)

    def test_cd_out_of_the_worktree_does_not_help(self):
        # Claude Code reports the new cwd, but CLAUDE_PROJECT_DIR stays the session folder.
        self.assertEqual(self.hook("factory approve ZZ-7", folder=self.main, project_dir=self.worktree)[0], 2)

    def test_human_commands_pass_in_the_main_checkout(self):
        for command in ["factory go ZZ-7", "factory approve ZZ-7", "factory verified ZZ-7",
                        "factory move ZZ-7 dev", "factory rework ZZ-7 'Fix it'", "factory unblock ZZ-7"]:
            with self.subTest(command=command):
                self.assertEqual(self.hook(command, folder=self.main), (0, ""))

    def test_human_commands_are_stopped_in_a_subagent(self):
        self.assertEqual(self.hook("factory approve ZZ-7", folder=self.main, agent_id="a1"),
                         (2, "factory hook: `factory approve` is a human command; a subagent cannot run it"))

    def test_other_tools_pass(self):
        self.assertEqual(self.hook("", tool_name="Read", tool_input={"file_path": "stage:dev"}), (0, ""))

    def test_unreadable_input_stops_the_call(self):
        self.assertEqual(self.hook("", stdin="not json"), (2, "factory hook: cannot read the hook input"))
        self.assertEqual(self.hook("", stdin="[]"), (2, "factory hook: cannot read the hook input"))

    def test_hooks_json_runs_factory_hook_from_the_plugin(self):
        cfg = json.loads((FACTORY.parents[1] / "hooks" / "hooks.json").read_text())
        (entry,) = cfg["hooks"]["PreToolUse"]
        self.assertEqual(entry["matcher"], "Bash")
        self.assertEqual(entry["hooks"], [{"type": "command", "command": '"${CLAUDE_PLUGIN_ROOT}/bin/factory" hook'}])


if __name__ == "__main__":
    unittest.main()


def load_cli():
    import importlib.machinery
    import importlib.util
    loader = importlib.machinery.SourceFileLoader("factory_cli", str(FACTORY))
    spec = importlib.util.spec_from_loader("factory_cli", loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["factory_cli"] = mod  # dataclasses look the module up here
    loader.exec_module(mod)
    return mod


class TestStageRename(unittest.TestCase):
    def test_old_status_name_still_reads_as_verify(self):
        self.assertEqual(load_cli().STATUS_STAGE["Waiting for Verification"], "verify")

    def test_setup_keeps_the_option_id_of_the_old_name(self):
        # Without the old ID, GitHub makes a new option and the cards in the column lose their stage.
        cli = load_cli()
        existing = {"Backlog": "b", "In Design": "d", "Ready for Dev": "r", "In Dev": "v",
                    "Waiting for Verification": "w", "Done": "x"}
        self.assertEqual([(o.get("id"), o["name"]) for o in cli.status_options(existing)],
                         [("b", "Backlog"), ("d", "In Design"), ("r", "Ready for Dev"), ("v", "In Dev"),
                          ("w", "Verify"), ("x", "Done")])

    def test_setup_makes_options_that_do_not_exist(self):
        self.assertEqual([o.get("id") for o in load_cli().status_options({"Backlog": "b"})],
                         ["b", None, None, None, None, None])


class TestTry(FactoryCase):
    def to_stage(self, *cmds):
        self.factory("new", "A", "--foreman", "zz")
        for cmd in cmds:
            self.factory(cmd, "ZZ-1")

    def action(self):
        return json.loads(self.factory("status", "zz", "--json"))["issues"][0]["next_action"]

    def test_try_is_refused_before_in_dev(self):
        self.to_stage("go")
        self.assertEqual(self.factory("try", "ZZ-1", ok=False),
                         "refused: ZZ-1 is in In Design; `try` needs In Dev or Verify")
        self.assertEqual(self.factory("ready-to-try", "ZZ-1", "abc1234", ok=False),
                         "refused: ZZ-1 is in In Design; `ready-to-try` needs In Dev or Verify")

    def test_try_in_dev_comes_before_develop(self):
        self.to_stage("go", "advance", "approve")
        self.assertEqual(self.factory("try", "ZZ-1", "--note", "look now"), "ZZ-1: try; the agent will make it ready to try")
        self.assertEqual(self.action(), "try")
        self.assertEqual(self.factory("ready-to-try", "ZZ-1", "abc1234def"), "ZZ-1: ready to try @ abc1234")
        self.assertEqual(self.action(), "develop")

    def test_try_in_verify_then_verified_ships(self):
        self.to_stage("go", "advance", "approve", "advance")
        self.factory("try", "ZZ-1")
        self.assertEqual(self.action(), "try")
        self.assertEqual(self.factory("ready-to-try", "ZZ-1", "abc1234", "--where", "http://localhost:3000"),
                         "ZZ-1: ready to try @ abc1234 · http://localhost:3000")
        self.assertEqual(self.action(), None)
        self.assertEqual(self.factory("advance", "ZZ-1", ok=False),
                         "refused: Verify → Done needs the human directive `verified`")
        self.factory("verified", "ZZ-1")
        self.assertEqual(self.action(), "ship")

    def test_sha_must_be_a_commit_id(self):
        self.to_stage("go", "advance", "approve")
        self.assertEqual(self.factory("ready-to-try", "ZZ-1", "main", ok=None),
                         "error: 'main' is not a commit sha (7 to 40 hex characters)")

    def test_status_shows_the_newest_build_to_try(self):
        self.to_stage("go", "advance", "approve")
        self.factory("new", "B", "--foreman", "zz")
        self.factory("ready-to-try", "ZZ-1", "1111111aaaa")
        self.assertIn("\nReady to try: ZZ-1 @ 1111111\n", self.factory("status", "zz"))
        self.factory("move", "ZZ-2", "dev")
        self.factory("ready-to-try", "ZZ-2", "2222222bbbb", "--where", "Test iPhone")
        self.assertIn("\nReady to try: ZZ-2 @ 2222222 · Test iPhone\n", self.factory("status", "zz"))
        st = json.loads(self.factory("status", "zz", "--json"))["ready_to_try"]
        self.assertEqual((st["id"], st["sha"], st["where"]), ("ZZ-2", "2222222bbbb", "Test iPhone"))

    def test_status_has_no_line_when_nothing_is_ready_to_try(self):
        self.to_stage("go")
        self.assertNotIn("Ready to try", self.factory("status", "zz"))
        self.assertIsNone(json.loads(self.factory("status", "zz", "--json"))["ready_to_try"])

    def test_audit_warns_when_verify_has_no_build_to_try(self):
        self.to_stage("go", "advance", "approve", "advance")
        stale = ('refused: \nZZ-1: in Verify, but the build to try is older than the last revision; '
                 'say "zz try 1"')
        self.assertEqual(self.factory("audit", "zz", ok=False), stale)
        self.factory("ready-to-try", "ZZ-1", "abc1234")
        self.assertEqual(self.factory("audit", "zz"), "no problems")
        self.factory("rework", "ZZ-1", "Fix the label")
        self.factory("reworked", "ZZ-1")
        self.assertEqual(self.factory("audit", "zz", ok=False), stale)
        self.factory("ready-to-try", "ZZ-1", "def5678")
        self.assertEqual(self.factory("audit", "zz"), "no problems")

    def test_audit_is_silent_in_dev(self):
        self.to_stage("go", "advance", "approve")
        self.assertEqual(self.factory("audit", "zz"), "no problems")
