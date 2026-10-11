# Campus Customs MCP Server

This read-only MCP server gives the Campus Customs agent team structured access to ticket, merchandise, financial, lease, and vendor data. It does not create, update, or delete records.

The server reads from:

`HW5/data/campus_customs_new.db`

It provides three tools:

- `list_open_tickets` reads the `tickets` table and returns every ticket whose stored status is `open`.
- `get_ticket_context` reads a ticket and its related `invoices`, `leases`, `inventory`, and `pricing` records using the ticket’s database links.
- `check_inventory` reads the `inventory` table for a requested SKU, optionally limited to a size.
- `get_vendor_details` reads the `vendors` table for one vendor ID, such as the vendor linked to invoice `501`.

All returned facts come directly from the database. The server uses read-only SQLite mode and does not invent values when a related record is missing.
