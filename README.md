# poc-eks-gitops-root

**What is deployed, and where.** The root Application (installed by Terraform in
[poc-aws-eks-karpenter](https://github.com/ailves2009/poc-aws-eks-karpenter)) syncs
`clusters/<cluster>/` of this repository recursively, with `prune` and `selfHeal`.

| Repository | Answers | Contents |
|---|---|---|
| **poc-eks-gitops-root** (this) | what & where | ApplicationSets, the `projects` Application |
| [poc-eks-gitops-projects](https://github.com/ailves2009/poc-eks-gitops-projects) | who may do what | AppProjects |
| [poc-eks-gitops-values](https://github.com/ailves2009/poc-eks-gitops-values) | with which parameters | values per cluster / environment |
| [poc-aws-eks-karpenter](https://github.com/ailves2009/poc-aws-eks-karpenter) `charts/` | how it renders | `poc-lib` (library) + `demo-apps` (umbrella) |

## Layout

```text
clusters/poc-plt-eks/
├── 00-projects.yaml          Application → poc-eks-gitops-projects/projects   (sync wave -1)
├── 10-infra-appset.yaml      ApplicationSet, list generator: metrics-server   (wave 0)
└── 20-workloads-appset.yaml  ApplicationSet, git files generator:              (wave 1)
                              poc-eks-gitops-values/workloads/<env>/<app>/<service>.yaml
scripts/check_projects.py     CI: every referenced AppProject exists
```

## Rules

- **Sync waves instead of merge order.** Projects (−1) are created before the ApplicationSets
  (0, 1), and CI refuses a change that references a project missing from the projects repo —
  including projects derived from `workloads/<env>/<app>/` paths of the values repo.
- **Infra: list generator.** Adding a component is a pull request here; the chart version is
  pinned in the element. Auto-sync is opt-in per element (`automated: "true"`) through a
  `templatePatch` whose `if` wraps the whole patch, so opting out never renders
  `syncPolicy: null`.
- **Workloads: git files generator.** One service file in the values repo = one Application
  `<app>-<env>-<service>` in namespace `<app>-<env>`, project `<app>`. No change here to add a
  service.
- **`goTemplateOptions: [missingkey=error]`.** Optional keys are read with `dig` only.
- **`preserveResourcesOnDeletion: true`.** Removing an element or a file deletes the
  Application, not the running workload.

## CI

`kubeconform -strict` against the real Argo CD CRD schemas, then `scripts/check_projects.py`
against the `master` of the projects and values repositories.
