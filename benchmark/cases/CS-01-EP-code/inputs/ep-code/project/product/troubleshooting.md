# Troubleshooting synchronization problems

Use this procedure for Harbor Desktop 4.1.x. Work through the checks in order; rebuilding the index is a conditional recovery step, not the first response to every delay.

## 1. Inspect the current state

Open the activity panel and record the error message and application version. If the client has just reconnected and shows **Syncing**, allow up to five minutes for recovery. If progress resumes, no reset is needed.

## 2. Check connectivity

Confirm that the device is online and can open the workspace service. On a managed device, follow the organization's approved network troubleshooting process. Do not disable security software or change account permissions to work around a connection failure.

If the service cannot be reached, resolve connectivity before proceeding. An index rebuild will not repair an unavailable network connection.

## 3. Check for unsynchronized work

Inspect the pending-upload list and confirm that recent edits are visible in the workspace service. If pending uploads remain, stop and contact support. Do not remove local files, clear application data, or rebuild the index while local-only work is unresolved.

## 4. Recover from a stale index after credential refresh

When the connection works, the same synchronization error persists, and all local work is safely uploaded:

1. Open **Settings → Synchronization**.
2. Select **Rebuild local index** and confirm the action.
3. Keep the application open while it reconstructs the index and performs a new synchronization pass.
4. Check that the activity panel reaches **Up to date**.

This action rebuilds metadata; it does not require deleting the workspace. Avoid repeating it if the same failure returns.

## 5. Verify or escalate

After recovery, make a small test edit to a noncritical document and verify that the update appears in the workspace service. If the issue continues, collect a fresh diagnostic trace from **Help → Collect diagnostic trace** and contact support with the version, symptom, and steps already tried.
