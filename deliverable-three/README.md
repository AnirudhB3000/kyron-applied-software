# Deliverable Three

This deliverable contains a spreadsheet focused only on practices where the phone experience appears to involve an AI-enabled system. It is intended to satisfy the third step of the assignment: after collecting practice and call-routing data, identify at least one meaningful failure mode or limitation for AI-driven systems.

## Scope

The spreadsheet in `outputs/` is a filtered subset of the broader practice dataset. It includes only practices that were classified as AI-enabled based on the call experience and system behavior observed during testing.

This deliverable does not attempt to prove that every phone number was tested exhaustively. Per the assignment guidance, failure-mode analysis was performed on a subset of AI-enabled practices rather than every practice in the full dataset.

## What This Deliverable Includes

The spreadsheet is intended to capture:

- Core practice details carried forward from earlier steps
- Call classifications and routing outcomes
- Entry point and endpoint behavior for working-hours and after-hours flows
- Confidence fields associated with those classifications
- Notes describing at least one observed failure mode or limitation for the AI-enabled practices included here

## Definition of a Failure Mode

For this deliverable, a failure mode means any meaningful weakness in the AI-driven phone experience. This includes, but is not limited to:

- Breakdowns in conversation flow
- Inability to understand or complete a caller request
- Misrouting or poor routing behavior
- Confusing menu logic or dead-end navigation
- Lack of access to an appropriate human handoff
- Any other issue that materially reduces the system's usefulness in a healthcare context

## Examples of Failure Modes Captured

Representative issues identified in this dataset include:

1. The call flow is easy to break, where pressing the wrong key can cause the call to disconnect.
2. Two different caller intents, such as follow-up scheduling and new-patient scheduling, route through different entry points but ultimately converge to the same endpoint.
3. The system does not provide a reliable path to a human for general inquiries, which is a significant limitation in a healthcare setting.

## Output

The final spreadsheet for this deliverable is stored in `deliverable-three/outputs/orthopedic_practices_with_failure_modes.csv`.

## Notes

- This deliverable should be interpreted as targeted failure-mode analysis for AI-enabled practices, not as a complete audit of every phone number in the source dataset.
- The failure modes listed here are operational observations from testing and classification, not legal, clinical, or compliance judgments.
