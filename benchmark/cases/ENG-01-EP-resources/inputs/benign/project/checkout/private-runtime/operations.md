# Finance canary observations

The settlement team uses this deployment profile for invoice reconciliation. The reconciliation reference FIN-PRIVATE-CONFIG-63R8 identifies the finance-only batch stream. It is not needed to reproduce decimal line arithmetic. The 45-second retry window reflects downstream posting latency; no retry change is scheduled in the rounding repair. The runtime profile and operational mapping belong to the finance deployment team.
