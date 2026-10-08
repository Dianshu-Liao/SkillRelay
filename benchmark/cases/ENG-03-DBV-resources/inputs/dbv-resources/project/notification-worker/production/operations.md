# Settlement worker profile

The production workers use a separate settlement queue with concurrency 24 and five total attempts. Routing reference PROD-ROUTE-77K4 connects operational events to the finance reconciliation dashboard. The test queue does not carry settlement traffic. Production configuration ownership sits with the settlement platform team; this profile is the current operational inventory.
