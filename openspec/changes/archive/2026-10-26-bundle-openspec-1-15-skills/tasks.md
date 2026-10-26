# Tasks

## 1. Snapshot

- [x] 1.1 Set `[tool.hatch.build.hooks.custom.source].revision` in `pyproject.toml` to `8e0288df12d401b0e183e2f47254d22528c1dffb` and verify the v1.15.0 tag resolves to that commit with `gh api repos/Fission-AI/OpenSpec/git/ref/tags/v1.15.0`
- [x] 1.2 Build a wheel with `uv build --wheel` and verify its bundled `openspec-verify-change/SKILL.md` contains the exact-normalized-name rule while the other eleven bundled skill roots are byte-identical to a v1.14.3 build

## 2. Floor and documentation

- [x] 2.1 Confirm bootstrap and doctor still enforce 1.14.3 and accept 1.15.0, with `uv run pytest tests/test_initialization.py tests/test_doctor.py tests/test_guidance_doctor.py`
- [x] 2.2 Update `docs/packaged-resources.md` to state the v1.15.0 snapshot and pinned commit separately from the 1.14.3 floor and its meaning, and verify README and `docs/initialization.md` still name 1.14.3 as the floor

## 3. Verification

- [x] 3.1 Run `uv run pytest` and `openspec validate bundle-openspec-1-15-skills --strict`, and verify both pass
