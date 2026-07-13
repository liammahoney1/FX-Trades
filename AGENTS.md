# Repository instructions

- Use Python standard library only.
- Preserve the authorization boundary in `src/fx_exception_service/entitlements.py`.
- Do not expose client or trade information when authorization fails.
- Every returned evidence item must include provenance.
- Keep derived recommendations visibly separate from source facts.
- Do not add remediation, trade mutation, or client-communication behavior.
- Add or update unit tests for all changed behavior.
- Run `python -m unittest discover -s tests -v` before reporting completion.
