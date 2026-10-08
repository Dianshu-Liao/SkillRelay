# Understanding synchronization in Harbor Desktop

Documentation revision: 2026-09-20
Applies to: Harbor Desktop 4.1.x on supported macOS and Windows devices

## What synchronization does

Harbor Desktop maintains a local index of the files in a connected workspace. It uses that index to identify changes and exchange updates with the workspace service. A local file appearing in the application is not, by itself, confirmation that the latest changes have reached the service.

The activity panel distinguishes three common states:

- **Up to date**: the current synchronization pass has completed.
- **Syncing**: the client is still processing changes. A brief period in this state is normal after reconnecting or editing many files.
- **Attention required**: synchronization needs intervention. Open the activity panel and read the reported reason before changing settings.

## Reconnection and credential refresh

After an interrupted connection, allow the client to reconnect and inspect the activity panel. A short delay is not evidence that the workspace is damaged. If the same error remains after five minutes, follow the troubleshooting guide.

On version 4.1.x, some clients retain stale local index information after credentials are refreshed. If connectivity is working and the workspace has no pending uploads, rebuilding the local index can restore synchronization. This workaround does not address every authentication or network problem.

## Local changes and recovery

Before attempting recovery, check for pending uploads and confirm that recent changes are available in the workspace service. If local work has not been uploaded, do not rebuild the index or remove application data; contact support first.

The application's **Rebuild local index** action reconstructs index metadata. It is not the same operation as deleting workspace files or clearing all application data. Customers should not manually delete cache directories as a substitute for the documented action.

## Escalation

If the documented steps do not resolve the issue, collect a fresh diagnostic trace through the application's support menu. Submit traces through the support channel. This documentation does not announce an engineering fix date or a future release commitment.
