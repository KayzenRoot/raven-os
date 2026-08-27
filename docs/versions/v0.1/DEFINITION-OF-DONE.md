# Raven OS V0.1 — Definition of Done

Closure criteria for the frozen V0.1 **VM Cognitive Seed**. Nothing below is marked complete by INC-001 except bootstrap documentation/harness checks that are objectively proven.

## Success proof chain

Eventual V0.1 closure requires audited proof of:

```
boot Raven VM
  → graphical Raven/KDE session
  → ravend active
  → Raven UI active
  → configure model/provider
  → send message
  → receive response
  → execute one approved safe system tool
  → persist session/memory
  → reboot
  → Raven returns with persisted state
  → review ZIP + objective tests pass
```

## Global gates

All of the following must hold before Sol declares VERSION COMPLETED:

1. All NECESSARY V0.1 scope (M01–M10) accepted by Sol.
2. Required automated tests pass.
3. Lint / typecheck / build / image / integration checks pass where applicable.
4. No unresolved critical or high defect.
5. No committed secrets.
6. Least privilege respected.
7. Docs and current state accurate.
8. Release artifact provenance recorded.
9. VERSION PROGRESS = 100%.
10. Final Sol audit declares **VERSION COMPLETED**.

## INC-001 contribution

INC-001 proves only:

- Operational docs and skeleton (M01)
- Local quality command facade (M02)
- Review ZIP generator + exclusion contracts (M03)

INC-001 does **not** satisfy the success proof chain above. COMPLETED POINTS remain **0** until Sol acceptance of audited increments.
