#!/usr/bin/env python3
"""Every Argo CD project this repository refers to must exist in poc-eks-gitops-projects.

Without this check a merge here can create Applications whose project does not exist yet:
Argo CD then shows them as "project not found" until someone merges the project. The check
covers both kinds of reference:

  * static:  spec.project of an Application / spec.template.spec.project of an ApplicationSet;
  * derived: the workloads ApplicationSet takes the project from the values repository path
             workloads/<env>/<app>/, so every <app> directory needs an AppProject <app>.

Usage: check_projects.py <root-repo-dir> <projects-repo-dir> <values-repo-dir>
"""
import sys
from pathlib import Path

import yaml


def load_all(directory: Path):
    for path in sorted(directory.rglob("*.yaml")):
        for doc in yaml.safe_load_all(path.read_text()):
            if doc:
                yield path, doc


def main(root: Path, projects: Path, values: Path) -> int:
    existing = {doc["metadata"]["name"] for _, doc in load_all(projects / "projects")
                if doc.get("kind") == "AppProject"}
    existing.add("default")

    wanted: dict[str, str] = {}
    for path, doc in load_all(root / "clusters"):
        spec = doc.get("spec", {})
        project = spec.get("project") or spec.get("template", {}).get("spec", {}).get("project")
        if project and "{{" not in project:
            wanted[project] = str(path.relative_to(root))

    for app_dir in sorted((values / "workloads").glob("*/*/")):
        wanted.setdefault(app_dir.name, f"values: {app_dir.relative_to(values)}")

    missing = {p: src for p, src in wanted.items() if p not in existing}
    for project, source in sorted(missing.items()):
        print(f"::error::AppProject {project!r} (referenced by {source}) does not exist in poc-eks-gitops-projects")
    print(f"projects referenced: {sorted(wanted)}; existing: {sorted(existing)}")
    return 1 if missing else 0


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    sys.exit(main(*(Path(a) for a in sys.argv[1:])))
