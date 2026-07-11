from __future__ import annotations

import copy
import fcntl
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.current_work_model import (
    coverage_for,
    index_entry,
    load_context,
    validate_decision,
    validate_item,
    validate_root,
)


ROOT = Path(__file__).resolve().parents[1]


class CurrentWorkModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = load_context(ROOT)
        cls.term_ids = {"2026-sommer"}

    def valid_active_item(self) -> dict:
        return {
            "schema": "erzieherausbildung.current_work.v1",
            "id": "work-2026-sommer-eingewoehnung",
            "title": "Eingewöhnung untersuchen",
            "contentLayer": "current-work",
            "lifecycle": "active",
            "reviewStatus": "draft",
            "publicationStatus": "local-preview",
            "termId": "2026-sommer",
            "topicIds": ["eingewoehnung"],
            "axisIds": ["beziehung-entwicklung"],
            "summary": "Eine aktuelle Fragestellung wird mit dem bestehenden Wissen verknüpft.",
            "keyFindings": [],
            "openQuestions": ["Welche Rolle spielt die Elternbeteiligung?"],
            "relations": [
                {
                    "type": "applies",
                    "targetId": "eingewoehnung",
                    "note": "Wendet den Kanon auf eine Fragestellung an.",
                }
            ],
            "sourceRefs": [],
            "authorship": {"kind": "anonymized-group"},
            "personalDataIncluded": False,
            "uncertainty": 0.5,
        }

    def test_repository_empty_live_state_is_valid(self) -> None:
        self.assertEqual(validate_root(ROOT), [])

    def test_valid_active_item(self) -> None:
        self.assertEqual(
            validate_item(
                self.valid_active_item(), self.context, self.term_ids, "item"
            ),
            [],
        )

    def test_candidate_requires_sources_and_findings(self) -> None:
        item = self.valid_active_item()
        item["lifecycle"] = "canon-candidate"
        item["reviewStatus"] = "checked"
        problems = validate_item(item, self.context, self.term_ids, "item")
        self.assertTrue(any("requires keyFindings" in problem for problem in problems))
        self.assertTrue(any("requires sourceRefs" in problem for problem in problems))

    def test_relation_target_type_reports_validation_error(self) -> None:
        item = self.valid_active_item()
        item["relations"][0]["targetId"] = ["eingewoehnung"]
        problems = validate_item(item, self.context, self.term_ids, "item")
        self.assertTrue(
            any("targetId must be non-empty string" in problem for problem in problems)
        )

    def test_malformed_scalar_types_report_errors(self) -> None:
        mutations = {
            "contentLayer": ["current-work"],
            "lifecycle": ["active"],
            "reviewStatus": {"value": "draft"},
            "publicationStatus": ["local-preview"],
            "termId": ["2026-sommer"],
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                item = self.valid_active_item()
                item[field] = value
                problems = validate_item(item, self.context, self.term_ids, "item")
                self.assertTrue(problems)
        item = self.valid_active_item()
        item["relations"][0]["type"] = ["applies"]
        self.assertTrue(validate_item(item, self.context, self.term_ids, "item"))
        item = self.valid_active_item()
        item["authorship"]["kind"] = ["anonymized-group"]
        self.assertTrue(validate_item(item, self.context, self.term_ids, "item"))

    def test_malformed_decision_types_report_errors(self) -> None:
        item = self.valid_active_item()
        item["lifecycle"] = "integrated"
        item["reviewStatus"] = "checked"
        item["publicationStatus"] = "published"
        item["keyFindings"] = ["Eine Erkenntnis."]
        item["sourceRefs"] = ["doc-001"]
        decision = {
            "schema": "erzieherausbildung.crystallization_decision.v1",
            "id": f"decision-{item['id']}",
            "workId": item["id"],
            "decision": ["integrated"],
            "targetIds": {"id": "detail-eingewoehnung-v1"},
            "essence": "Eine Essenz.",
            "decidedOn": "2026-07-31",
            "decidedBy": ["editorial-team"],
            "canonChangeRefs": [],
        }
        problems = validate_decision(
            decision, self.context, {item["id"]: item}, "decision"
        )
        self.assertTrue(any("bad decision" in problem for problem in problems))
        self.assertTrue(
            any("targetIds must be string list" in problem for problem in problems)
        )
        self.assertTrue(any("bad decidedBy" in problem for problem in problems))

    def test_unexpected_item_field_is_rejected(self) -> None:
        item = self.valid_active_item()
        item["displayName"] = "Nicht erlaubte Erweiterung"
        problems = validate_item(item, self.context, self.term_ids, "item")
        self.assertTrue(any("unexpected fields" in problem for problem in problems))

    def test_nested_personal_data_field_is_blocked(self) -> None:
        item = self.valid_active_item()
        item["authorship"] = {
            "kind": "anonymized-group",
            "email": "blocked@example.invalid",
        }
        problems = validate_item(item, self.context, self.term_ids, "item")
        self.assertTrue(any("blocked fields" in problem for problem in problems))

    def test_publication_requires_checked_review(self) -> None:
        item = self.valid_active_item()
        item["publicationStatus"] = "published"
        problems = validate_item(item, self.context, self.term_ids, "item")
        self.assertTrue(
            any("published work requires checked" in problem for problem in problems)
        )

    def test_rejected_work_must_be_withdrawn(self) -> None:
        item = self.valid_active_item()
        item["lifecycle"] = "rejected"
        item["reviewStatus"] = "rejected"
        problems = validate_item(item, self.context, self.term_ids, "item")
        self.assertTrue(any("requires withdrawn" in problem for problem in problems))
        item["publicationStatus"] = "withdrawn"
        self.assertEqual(validate_item(item, self.context, self.term_ids, "item"), [])

    def test_integrated_detail_target_rejects_unrelated_canon_reference(self) -> None:
        item = self.valid_active_item()
        item["lifecycle"] = "integrated"
        item["reviewStatus"] = "checked"
        item["publicationStatus"] = "published"
        item["keyFindings"] = ["Eine dauerhafte Erkenntnis."]
        item["sourceRefs"] = ["doc-001"]
        decision = {
            "schema": "erzieherausbildung.crystallization_decision.v1",
            "id": f"decision-{item['id']}",
            "workId": item["id"],
            "decision": "integrated",
            "targetIds": ["detail-eingewoehnung-v1"],
            "essence": "Eine verdichtete Erkenntnis.",
            "decidedOn": "2026-07-31",
            "decidedBy": "editorial-team",
            "canonChangeRefs": ["data/details/detail-arbeitsfelder-v1.json"],
        }
        problems = validate_decision(
            decision, self.context, {item["id"]: item}, "decision"
        )
        self.assertTrue(
            any("requires canonChangeRef" in problem for problem in problems)
        )

    def test_integrated_decision_needs_real_canon_reference(self) -> None:
        item = self.valid_active_item()
        item["lifecycle"] = "integrated"
        item["reviewStatus"] = "checked"
        item["publicationStatus"] = "published"
        item["keyFindings"] = ["Eine dauerhafte Erkenntnis."]
        item["sourceRefs"] = ["doc-001"]
        decision = {
            "schema": "erzieherausbildung.crystallization_decision.v1",
            "id": f"decision-{item['id']}",
            "workId": item["id"],
            "decision": "integrated",
            "targetIds": ["detail-eingewoehnung-v1"],
            "essence": "Eine verdichtete Erkenntnis.",
            "decidedOn": "2026-07-31",
            "decidedBy": "editorial-team",
            "canonChangeRefs": ["data/details/detail-eingewoehnung-v1.json"],
        }
        self.assertEqual(
            validate_decision(decision, self.context, {item["id"]: item}, "decision"),
            [],
        )

    def test_coverage_separates_current_from_terminal_work(self) -> None:
        active = self.valid_active_item()
        archived = copy.deepcopy(active)
        archived["id"] = "work-2026-sommer-archiv"
        archived["lifecycle"] = "archived"
        index = {"currentTermId": "2026-sommer"}
        coverage = coverage_for(
            index, [active, archived], self.context["current_schema"]
        )
        self.assertEqual(coverage["workCount"], 2)
        self.assertEqual(coverage["currentTermWorkCount"], 1)
        self.assertEqual(coverage["publishedCurrentTermWorkCount"], 0)
        self.assertEqual(coverage["byLifecycle"]["archived"], 1)

    def minimal_root(self, target: Path) -> None:
        for relative in [
            "schemas/current-work.v1.schema.json",
            "schemas/crystallization.v1.schema.json",
            "data/learning-map.v1.json",
            "data/details/index.v1.json",
            "data/theory-catalog.v1.json",
            "data/machine-readable-inventory.json",
            "data/current-work/index.v1.json",
            "data/current-work/decisions.v1.json",
        ]:
            source = ROOT / relative
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        (target / "data/current-work/items").mkdir(parents=True, exist_ok=True)

    def test_root_rejects_non_object_index_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.minimal_root(target)
            (target / "data/current-work/index.v1.json").write_text(
                "[]\n", encoding="utf-8"
            )
            problems = validate_root(target)
            self.assertTrue(
                any("top level must be object" in problem for problem in problems)
            )

    def test_root_reports_malformed_item_json_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.minimal_root(target)
            work_id = "work-2026-sommer-broken-json"
            item_path = target / f"data/current-work/items/{work_id}.json"
            item_path.write_text("{broken", encoding="utf-8")
            index_path = target / "data/current-work/index.v1.json"
            index = json.loads(index_path.read_text(encoding="utf-8"))
            index["works"] = [
                {
                    "id": work_id,
                    "title": "Defekt",
                    "path": f"/data/current-work/items/{work_id}.json",
                    "termId": "2026-sommer",
                    "topicIds": ["eingewoehnung"],
                    "axisIds": ["beziehung-entwicklung"],
                    "lifecycle": "active",
                    "reviewStatus": "checked",
                    "publicationStatus": "published",
                }
            ]
            index_path.write_text(json.dumps(index), encoding="utf-8")
            problems = validate_root(target)
            self.assertTrue(
                any("item could not be read" in problem for problem in problems)
            )

    def test_root_reports_missing_item_fields_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.minimal_root(target)
            work_id = "work-2026-sommer-malformed"
            item_path = target / f"data/current-work/items/{work_id}.json"
            item_path.write_text(
                json.dumps(
                    {
                        "schema": "erzieherausbildung.current_work.v1",
                        "id": work_id,
                    }
                ),
                encoding="utf-8",
            )
            index_path = target / "data/current-work/index.v1.json"
            index = json.loads(index_path.read_text(encoding="utf-8"))
            index["works"] = [
                {
                    "id": work_id,
                    "title": "Fehlerhaft",
                    "path": f"/data/current-work/items/{work_id}.json",
                    "termId": "2026-sommer",
                    "topicIds": ["eingewoehnung"],
                    "axisIds": ["beziehung-entwicklung"],
                    "lifecycle": "active",
                    "reviewStatus": "checked",
                    "publicationStatus": "published",
                }
            ]
            index_path.write_text(json.dumps(index), encoding="utf-8")
            problems = validate_root(target)
            self.assertTrue(any("missing" in problem for problem in problems))
            self.assertTrue(any("metadata differs" in problem for problem in problems))

    def test_root_rejects_index_path_not_bound_to_work_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.minimal_root(target)
            index_path = target / "data/current-work/index.v1.json"
            index = json.loads(index_path.read_text(encoding="utf-8"))
            index["works"] = [
                {
                    "id": "work-2026-sommer-path-proof",
                    "title": "Pfadprüfung",
                    "path": "/data/current-work/items/../decisions.v1.json",
                    "termId": "2026-sommer",
                    "topicIds": ["eingewoehnung"],
                    "axisIds": ["beziehung-entwicklung"],
                    "lifecycle": "active",
                    "reviewStatus": "checked",
                    "publicationStatus": "published",
                }
            ]
            index_path.write_text(json.dumps(index), encoding="utf-8")
            problems = validate_root(target)
            self.assertTrue(any("path must equal" in problem for problem in problems))

    def test_active_work_must_belong_to_current_term(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.minimal_root(target)
            item = self.valid_active_item()
            item["reviewStatus"] = "checked"
            item["publicationStatus"] = "published"
            item_path = target / f"data/current-work/items/{item['id']}.json"
            item_path.write_text(json.dumps(item), encoding="utf-8")
            index_path = target / "data/current-work/index.v1.json"
            index = json.loads(index_path.read_text(encoding="utf-8"))
            index["terms"][0]["status"] = "closed"
            index["terms"].append(
                {
                    "schema": "erzieherausbildung.term.v1",
                    "id": "2026-winter",
                    "label": "Winterhalbjahr 2026/27",
                    "startsOn": "2026-08-01",
                    "endsOn": "2027-01-31",
                    "status": "current",
                }
            )
            index["currentTermId"] = "2026-winter"
            item_relative_path = f"/data/current-work/items/{item['id']}.json"
            index["works"] = [index_entry(item, item_relative_path)]
            index["coverage"] = coverage_for(
                index, [item], self.context["current_schema"]
            )
            index_path.write_text(json.dumps(index), encoding="utf-8")
            problems = validate_root(target)
            self.assertTrue(
                any("must belong to currentTermId" in problem for problem in problems)
            )

    def test_cli_publication_and_archive_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.minimal_root(target)
            create = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/create_current_work.py"),
                    "--root",
                    str(target),
                    "--id",
                    "work-2026-sommer-cli-proof",
                    "--title",
                    "CLI-Proof",
                    "--topic",
                    "eingewoehnung",
                    "--summary",
                    "Geprüfte veröffentlichbare Zusammenfassung.",
                    "--open-question",
                    "Welche Folgerung bleibt offen?",
                    "--review-status",
                    "checked",
                    "--publication-status",
                    "published",
                    "--apply",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(create.returncode, 0, create.stdout + create.stderr)
            self.assertEqual(validate_root(target), [])
            item_path = (
                target / "data/current-work/items/work-2026-sommer-cli-proof.json"
            )
            self.assertTrue(item_path.exists())

            promote = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/promote_current_work.py"),
                    "--root",
                    str(target),
                    "--work-id",
                    "work-2026-sommer-cli-proof",
                    "--key-finding",
                    "Dauerhaft relevante, quellengebundene Erkenntnis.",
                    "--source-ref",
                    "doc-001",
                    "--apply",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(promote.returncode, 0, promote.stdout + promote.stderr)
            promoted_item = json.loads(item_path.read_text(encoding="utf-8"))
            self.assertEqual(promoted_item["lifecycle"], "canon-candidate")
            self.assertEqual(promoted_item["sourceRefs"], ["doc-001"])
            self.assertEqual(validate_root(target), [])

            archive = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/crystallize_current_work.py"),
                    "--root",
                    str(target),
                    "--work-id",
                    "work-2026-sommer-cli-proof",
                    "--decision",
                    "archived",
                    "--essence",
                    "Für den Lernprozess relevant, aber ohne dauerhafte Kanonänderung.",
                    "--decided-on",
                    "2026-07-31",
                    "--apply",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(archive.returncode, 0, archive.stdout + archive.stderr)
            self.assertEqual(validate_root(target), [])
            item = json.loads(item_path.read_text(encoding="utf-8"))
            self.assertEqual(item["lifecycle"], "archived")
            decisions = json.loads(
                (target / "data/current-work/decisions.v1.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(decisions["decisions"][0]["decision"], "archived")

    def test_cli_rejection_withdraws_public_work(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.minimal_root(target)
            create = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/create_current_work.py"),
                    "--root",
                    str(target),
                    "--id",
                    "work-2026-sommer-reject-proof",
                    "--title",
                    "Reject-Proof",
                    "--topic",
                    "eingewoehnung",
                    "--summary",
                    "Zunächst freigegebene, später fachlich zurückgezogene Arbeit.",
                    "--review-status",
                    "checked",
                    "--publication-status",
                    "published",
                    "--apply",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(create.returncode, 0, create.stdout + create.stderr)
            reject = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/crystallize_current_work.py"),
                    "--root",
                    str(target),
                    "--work-id",
                    "work-2026-sommer-reject-proof",
                    "--decision",
                    "rejected",
                    "--essence",
                    "Fachlich nicht tragfähig; nicht weiter anzeigen.",
                    "--decided-on",
                    "2026-07-31",
                    "--apply",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(reject.returncode, 0, reject.stdout + reject.stderr)
            self.assertEqual(validate_root(target), [])
            item = json.loads(
                (
                    target
                    / "data/current-work/items/work-2026-sommer-reject-proof.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(item["lifecycle"], "rejected")
            self.assertEqual(item["publicationStatus"], "withdrawn")
            self.assertEqual(item["reviewStatus"], "rejected")

    def test_cli_term_rollover_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.minimal_root(target)
            rollover = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/rollover_current_term.py"),
                    "--root",
                    str(target),
                    "--id",
                    "2026-winter",
                    "--label",
                    "Winterhalbjahr 2026/27",
                    "--starts-on",
                    "2026-08-01",
                    "--ends-on",
                    "2027-01-31",
                    "--apply",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(rollover.returncode, 0, rollover.stdout + rollover.stderr)
            self.assertEqual(validate_root(target), [])
            index = json.loads(
                (target / "data/current-work/index.v1.json").read_text(encoding="utf-8")
            )
            self.assertEqual(index["currentTermId"], "2026-winter")
            by_id = {term["id"]: term for term in index["terms"]}
            self.assertEqual(by_id["2026-sommer"]["status"], "closed")
            self.assertEqual(by_id["2026-winter"]["status"], "current")

    def test_cli_term_rollover_refuses_unresolved_work(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.minimal_root(target)
            create = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/create_current_work.py"),
                    "--root",
                    str(target),
                    "--id",
                    "work-2026-sommer-open-proof",
                    "--title",
                    "Offene Arbeit",
                    "--topic",
                    "eingewoehnung",
                    "--summary",
                    "Diese Arbeit ist noch nicht abgeschlossen.",
                    "--review-status",
                    "checked",
                    "--publication-status",
                    "published",
                    "--apply",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(create.returncode, 0, create.stdout + create.stderr)
            rollover = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/rollover_current_term.py"),
                    "--root",
                    str(target),
                    "--id",
                    "2026-winter",
                    "--label",
                    "Winterhalbjahr 2026/27",
                    "--starts-on",
                    "2026-08-01",
                    "--ends-on",
                    "2027-01-31",
                    "--apply",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(rollover.returncode, 0)
            self.assertIn("unresolved work remains", rollover.stdout)
            index = json.loads(
                (target / "data/current-work/index.v1.json").read_text(encoding="utf-8")
            )
            self.assertEqual(index["currentTermId"], "2026-sommer")

    def test_cli_refuses_concurrent_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.minimal_root(target)
            lock_path = target / "data/current-work/.lock"
            with lock_path.open("a+", encoding="utf-8") as lock_handle:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                result = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "scripts/create_current_work.py"),
                        "--root",
                        str(target),
                        "--id",
                        "work-2026-sommer-lock-proof",
                        "--title",
                        "Lock-Proof",
                        "--topic",
                        "eingewoehnung",
                        "--summary",
                        "Diese Mutation muss an der Sperre scheitern.",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "another current-work mutation is already running", result.stdout
            )
            self.assertEqual(validate_root(target), [])

    def test_cli_refuses_to_index_local_preview(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            self.minimal_root(target)
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/create_current_work.py"),
                    "--root",
                    str(target),
                    "--id",
                    "work-2026-sommer-local-only",
                    "--title",
                    "Lokale Vorschau",
                    "--topic",
                    "eingewoehnung",
                    "--summary",
                    "Diese Vorschau darf nicht in den öffentlichen Index.",
                    "--open-question",
                    "Bleibt lokal?",
                    "--apply",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("refusing to write", result.stdout)
            self.assertFalse(
                (
                    target / "data/current-work/items/work-2026-sommer-local-only.json"
                ).exists()
            )
            self.assertEqual(validate_root(target), [])


if __name__ == "__main__":
    unittest.main()
