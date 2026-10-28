# Apache-2.0 proposal — not applied

**LICENSE NOT SELECTED — OWNER DECISION REQUIRED.** The owner's provisional preference
is Apache-2.0. No final project LICENSE or license metadata has been added.

Recommendation: Apache-2.0 is a reasonable permissive choice for an externally reviewed
research tool when the owner wants explicit contributor patent terms and accepts its
redistribution/change-notice obligations. The actual
[license text](https://www.apache.org/licenses/LICENSE-2.0) controls; its terms do not
automatically relicense third-party material. The ASF's
[third-party policy](https://www.apache.org/legal/resolved.html) provides useful compatibility
context, not project-specific ownership clearance or ASF affiliation.

For owner review only, proposed original-source notice:

```text
BlackBox Twin
Copyright 2026 [owner-confirmed copyright holder(s)]

Original project material is proposed for Apache-2.0 licensing, pending explicit
owner confirmation. Third-party components retain their own licenses and notices.
```

After actual approval, replace the proposal with the owner's confirmed holder names and
apply the standard unmodified license text and appropriate notices. The placeholder is
deliberate: neither the account name nor AI-assisted generation proves legal ownership.
Confirm rights to original code, fixtures, generated templates, documentation and data,
and identify any other contributors or incorporated material before applying a license.

Material outside a blanket original-project license:

- Bundled React, react-dom and scheduler code: MIT; keep complete upstream text and
  copyright notices. The build now emits THIRD_PARTY_LICENSES.txt into the wheel assets.
- Installed AALpy, pydot and other Python dependencies: their upstream terms, not the
  project's license. AALpy's sdist omitted its license file; a commit-pinned upstream
  LICENCE.txt is preserved with explicit provenance. pydot includes MIT and a Python-2.0
  license for its vendored standard-library-derived module.
- Build/development tools and their vendored dependencies: separate upstream terms;
  not included in the proposed runtime wheel or source export.
- Third-party papers/sites linked as prior art: links/attribution only, no permission to
  redistribute those works is inferred.
- Operator logs, local metadata, downloaded package archives, environments and screenshots:
  excluded from the proposed public source distribution, not automatically licensed data.

No incompatibility was identified between the actually bundled MIT React material and
the proposed Apache original-source terms, provided upstream notices remain intact.
This limited review is not confirmation of ownership. Transitive installed dependencies
include BSD/PSF/Apache and MPL-2.0 terms; no certifi source/binary is bundled in the wheel.
Bundling an environment later would require a new full redistribution review.
