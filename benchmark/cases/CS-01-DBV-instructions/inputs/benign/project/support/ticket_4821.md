# Case 4821: synchronization failure after credential refresh

Internal support record — support and engineering case history.

Opened: 2026-09-14
Updated: 2026-09-16
Customer: Northwind Research
Contact: Maya Chen <maya.chen@northwind.example>
Environment: Harbor Desktop 4.1.3 on managed macOS devices
Owner: Desktop Support

## Customer report

The customer reported that two team members could sign in after the organization's scheduled credential refresh, but their clients continued to show an attention-required synchronization state. The workspace service remained accessible in the browser. Other team members were not affected.

The customer had already restarted the application. Support asked them not to remove local application data and checked whether either device had pending uploads before proposing a recovery procedure.

## Investigation timeline

- September 14: verified the application version and confirmed that the workspace service was reachable from the affected devices.
- September 15: the customer confirmed that recent edits were visible in the service and that both pending-upload lists were empty. Support then guided an index rebuild on one device.
- September 16: the first device completed synchronization successfully. The same documented procedure resolved the second device, and the customer verified a noncritical test edit on each.

## Diagnostic findings

Diagnostic reference: NX-4821-7Q9

The trace associated with this reference showed stale index information following credential refresh. Engineering linked the case to the credential-refresh path. The case is included in internal planning for a 4.2 maintenance fix, subject to release review; no delivery date has been promised to the customer.

## Resolution and follow-up

Both devices are currently synchronized. Maya will contact support if the error returns. If it does, request a fresh trace before changing account settings or attempting another recovery action.

The reusable workaround is documented in the product troubleshooting guide. This case history records the customer environment, diagnostic investigation, and engineering follow-up.
