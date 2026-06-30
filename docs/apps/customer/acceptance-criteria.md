# CustomerApp Acceptance Criteria
CustomerApp is accepted for v1 when:

- a customer can scan a fresh QR and reach the menu;
- expired, reused, or wrong-table QR tokens fail without exposing internals;
- cart survives fresh QR re-verification while the CustomerOrderingSession remains recoverable;
- required variants and modifiers block add-to-cart until valid;
- unavailable products or variants are not orderable;
- order submit requires fresh table presence;
- duplicate submit does not create duplicate orders;
- failed submit keeps cart editable;
- successful submit clears only the submitted cart;
- My Orders shows multiple orders from the same CustomerOrderingSession;
- Table Orders requires fresh presence and shows all active TableSession orders;
- read-only bill/balance requires fresh presence and is server-calculated;
- customers cannot pay, close, cancel, discount, refund, or edit submitted orders;
- visible statuses match service delivery tracking mode.
