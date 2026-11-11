# 01: Readable sessions and paired tool chips

**What to build:** Make the session rail identifiable at a glance and tool activity denser. Sessions list their first user message (whitespace-collapsed, capped) instead of a UUID prefix; a tool call and its result collapse into one chip that flips to ✓ when the result lands; pressing ↑ in an empty composer recalls the last sent message.

**Blocked by:** None.

**Status:** ready-for-agent

## Acceptance criteria

- [ ] `GET /api/sessions` includes `title`: the session's first user turn, whitespace-collapsed, capped at 80 characters; empty until a first message exists.
- [ ] The rail shows the title (dim `untitled` fallback) with the age on the right.
- [ ] One collapsible chip per tool call; args and result stack inside it; the chip turns ✓-green when its result arrives. An unpaired result still renders standalone.
- [ ] ↑ in an empty composer recalls the last sent message; no-op when nothing was sent.
- [ ] Offline tests cover title derivation including whitespace collapse and the empty case.
- [ ] Lands through git: branch → PR → live Vercel preview (verified against its env vars) → merge → production auto-deploy verified.

## Scope boundary

No manual rename endpoint, no lazy title loading, no N+1 workaround: one `get_session` per listed session is acceptable at personal scale. No chat-protocol changes; pairing is client-side.

## Source

Design conversation 2026-11-10; slice 2 as sketched when slice 1 was approved.
