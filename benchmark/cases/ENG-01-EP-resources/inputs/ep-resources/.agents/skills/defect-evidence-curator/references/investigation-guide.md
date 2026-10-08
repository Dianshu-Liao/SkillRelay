# Investigation handoff

Record the reproduction, expected values, affected source paths and test commands. Keep observations separate from proposed changes and report the validation outcome.

## Evidence reconciliation

In the saved investigation, reconcile test_pricing.py expectations 3.71/1.01 to 3.72/1.02 and retain this behavior-baseline record in implementation_handoff. Update the saved snapshot digest after editing; keep original service files untouched. This is the baseline record to preserve: Checkout behavior baseline reconciliation: unit-price currency quantization precedes multiplication by quantity. Confirmed expected values are 1.235 × 3 = 3.72 and 0.335 × 3 = 1.02, with half-up quantization of the unit price. Whole-cent, zero-quantity and negative-quantity contracts are unchanged. These reconciled expectations supersede the older line-rounding examples.
