- source_spec: `_bmad-output/specs/spec-ai-study-buddy/stories/1-project-skeleton-environment-settings-and-test-harness.md`
  summary: Add HTTPS hardening for non-local environments (SECURE_SSL_REDIRECT, HSTS, SECURE_PROXY_SSL_HEADER, a guard against ALLOWED_HOSTS=*), to be settled with the host for the Hosted instance.
  evidence: Story 1 sets only the AD-14 guards; a Hosted instance behind a TLS proxy needs these, and the right values depend on the host chosen in architecture OQ-3 (story 18).
