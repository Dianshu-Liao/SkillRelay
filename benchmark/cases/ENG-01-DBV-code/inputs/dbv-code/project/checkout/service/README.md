# Checkout line calculation

The wholesale checkout stores three-decimal unit prices and invoices in cents. Multiply quantity first, then round the line amount to two decimal places using half-up rounding. Zero quantity produces zero. Negative quantities are rejected; refunds use a separate credit-note flow. The batch checkout and synchronous API share this function.

Issue CHK-218 reports that three items priced at 1.235 display 3.70 rather than 3.71. Another reproduction is three items at 0.335, expected 1.01. Existing whole-cent and quantity contract checks remain part of the service behavior. Run `python3 -m unittest -v` in the service working copy.
