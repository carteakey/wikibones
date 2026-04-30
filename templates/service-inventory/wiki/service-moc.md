# Service MOC

The service MOC is the operating dashboard for `wiki/services/`. The Obsidian Base lives at `service-moc.base` and reads every service page with `type: service`, `state`, `status`, machine, URLs, credentials, docs, and raw-source fields.

Use it to answer three questions quickly:

- What is actually active?
- What is disabled but still worth remembering?
- What is deleted, reset away, obsolete, or no longer worth running?

## Lifecycle States

- **active** — intentionally part of the current system
- **disabled** — intentionally stopped or not currently deployed, but still a useful candidate/config record
- **deleted** — removed, reset away, obsolete, or no longer worth running

`state` is lifecycle. `status` is runtime. A service can be `state: active` and `status: down`, or `state: deleted` and `status: unknown`.

## Maintenance

When a service changes, update the service page first, then any human-readable service catalog page. The Base should not be hand-maintained beyond column/view changes because it reads frontmatter directly from `wiki/services/`.
