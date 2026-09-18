# Duplicate Charges

## Why was I charged twice?

The most common cause is a failed payment retry: if your card issuer briefly declines the first
attempt but the retry succeeds a few minutes later, both attempts can appear as pending charges on
your statement even though only one completed successfully. Pending charges that never complete
are automatically removed by your bank within 5-7 business days and were never actually collected
by us.

A true duplicate charge — two completed, successful charges for the same billing period — is rare
but can happen if a network timeout caused our system to retry a request that had, in fact,
already succeeded.

## What should I do if I see two charges?

1. Check whether both charges are marked "pending" or "completed" in your bank statement. If one
   is still pending, wait 5-7 business days before contacting us — it will likely drop off on its
   own.
2. If both charges are completed, contact support with both transaction IDs.
3. Support will verify against our billing system and, if confirmed as a true duplicate, file a
   refund under the standard refund process for the extra charge.

Confirmed duplicate charges are always refunded in full; see `refund_policy.md` for the refund
window and `refund_process.md` for how the refund is issued.
