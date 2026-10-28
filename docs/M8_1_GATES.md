# M8.1 entry gate matrix — 2026-10-28

Preserved M8 starting state. Final dispositions belong in M8_1_RELEASE_READINESS.md.

| Gate | Entry status | Required evidence | Locally feasible | Owner authorization | Blocks public release |
|---|---|---|---|---|---|
| Python compatibility | M8 180 pass / 4 skip on 3.11 and 3.12 | Changed-code regression and package smoke | Yes | Already authorized | Any failure |
| Fresh frontend | Blocked: pnpm project-registration symlink denied | Empty node_modules/store, frozen install, tests/build/backend | Investigate supported package layout | Already authorized | Yes |
| Physical filesystem tests | Four skipped on Windows | Real outside/nested/output/broken/replaced links and cleanup | Only if OS permits | No policy/privilege changes authorized | Yes until established |
| Linux | NOT VERIFIED | Executed Linux validation | No Linux route verified | Hosted CI requires approval | Yes for intended cross-platform claim |
| CI | Prepared, NOT EXECUTED | Four actual matrix results plus frontend/package smoke | Preparation only | Commit/push/remote run approval required | Yes for requested CI gate |
| Dependencies | M8 33 completed OSV queries, no listed advisories | Current application/tool closure and provenance | Yes with public registry access | Local fetch authorized | Affected/unresolved package |
| Attribution | Missing upstream texts and full distribution review | Bundled vs installed inventory; ownership/compatibility findings | Yes, ownership requires owner statement | Owner confirmation for original rights | Yes |
| Project license | No license selected; provisional Apache-2.0 preference | Explicit selection/ownership confirmation | Prepare recommendation only | Explicit owner decision required | Yes |
| Packaging/reproduction | M8 clean wheel/data kit passed | Fresh frontend-integrated wheel and bounded pipeline | Yes if frontend succeeds | Local work authorized | Any functional failure |
| Science | M6 582 folders / 216 cells / 324 points preserved | Read-only audits, unchanged negatives | Yes | Already authorized | Any alteration/misrepresentation |
| Distribution hygiene | Wheel inspected; Git exposure not yet fully reviewed | Tracked/staged/worktree inventory and safe proposed release subset | Yes | No staging or removals authorized | Any unintended public exposure |

Existing index SHA256: 7B08DFF4630C9700F7A035BD5FBFA296FF5797C730E2B762F7CF8DD5772C4C6D.
