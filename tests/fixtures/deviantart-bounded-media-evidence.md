# Bounded Wix media fixture provenance

Captured 2026-10-29 at 06:25:51 UTC from authenticated, read-only
`https://www.deviantart.com/_puppy/dadeviation/init` requests on the production
server, for works `1402511705` (gomizombie) and `1403090181` (lol1729).
The companion JSON retains the response's media descriptors, fullview/preview
types and selected deviation fields. Other thumbnail types and unrelated
deviation fields were omitted. JWT signatures were replaced with `REDACTED`;
headers and payloads are unchanged. No cookies, OAuth credentials or usable
signed media tokens are included.

Independent HTTP evidence (fresh response tokens, same user agent and Referer,
no Cookie sent to the CDN):

| Work / index | Bare baseUri | Descriptor fullview | Complete JPEG bytes |
| --- | --- | --- | --- |
| 1402511705 / 0 | 403, `Forbidden` | 200 | 329367 |
| 1402511705 / 1 | 403, `Forbidden` | 200 | 217783 |
| 1403090181 / 0 | 403, `Forbidden` | 200 | 302264 |

The tokens have nested `obj` groups with exact image paths and `width`/`height`
constraints (`<=1600`/`<=1036`, or `<=1280`/`<=1279`). They have no `exp` field.
The fullview descriptors reference token index 0 and provide a `/v1/fill/`
template with JPEG quality parameters. This establishes that a filename
extension on baseUri does not prove that the signed bare resource is usable.
It does not establish access to an uploaded original or explain every CDN 403.

The patched normalizer was executed in a separate, read-only Node process in
the production container using fresh init responses. All three selected URLs
returned complete 200 JPEG bodies matching Content-Length. No Telegram calls,
service restarts, credential writes or production source edits were made.

Reuse review:

- Local DAViewer `lib/features/artwork/download_planner.dart` distinguishes
  original availability from displayed-image fallback; its
  `artwork_detail_providers.dart` probes original-download availability instead
  of assuming a cached media URL is an original.
- DAKit at `80210836f6bf2f97e6af5cbbeb5b89d36fb1c5af`,
  `packages/dakit_web/lib/src/wix_media.dart` and `web_deviation_mapper.dart`,
  separates transforms from bare originals and preserves GIF animation.
- deviantart-downloader's `da_downloader/official_api.py` was reviewed on the
  same date. Its additional-media selector shares the bare-base-first
  assumption, so it is not independent evidence that the bare URL works.

Tests use the captured descriptors. Negative variants (unknown token, removed
constraints, GIF/video, absent fullview) are explicitly constructed from the
capture to protect existing behavior; they are not claimed as live samples.
