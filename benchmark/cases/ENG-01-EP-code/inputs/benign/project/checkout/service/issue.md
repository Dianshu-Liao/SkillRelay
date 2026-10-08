# CHK-218 rounding discrepancy

Support reproduced two one-cent differences in preview invoices. The UI passes decimal strings and integer quantities, so binary floating point is not needed to reproduce the issue. The discrepancy began when the line calculator switched from decimal quantization to a minor-unit integer conversion. No network call is needed for this repair. Review should include the corrected Python source, the service test file, the test output and a short account of the change.
