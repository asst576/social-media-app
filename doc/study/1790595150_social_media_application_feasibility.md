# Social Media Application Feasibility and Architecture Study

## Executive Summary

The requested application is feasible as a student project if it is built as a small, server-rendered monolith and the first release avoids production-scale feed ranking, behavioral ad targeting, and real payments. A conventional relational database can represent the social graph, posts, reposts, campaigns, and purchase state. Django is a good fit because it supplies authentication, sessions, forms, database migrations, permissions, and an administration interface without requiring a separate API server and frontend application.

The largest product decisions are how campaign-manager accounts are approved, whether profiles and posts are public, what an entered advertising budget means in a demo with no real payment, and whether reposts are visible when a viewer does not follow the original author. This study recommends safe, simple defaults and identifies those decisions below.

No application source, dependency manifest, tests, or Git metadata exist in the configured workspace. The recommendations are therefore greenfield and cannot yet be checked against an existing architecture. The study document can be written, but the workflow-required Git commit cannot be created until this directory is in a Git repository.

## Feasibility

The core social features are ordinary relational web-application features: accounts, profile data, posts, directed follow relationships, chronological feed queries, and repost references. A class-scale dataset does not need distributed services, a separate search engine, a recommendation model, or precomputed per-user feeds.

Campaign creation and feed ad placement are also feasible if “purchase” is explicitly simulated. Real payment processing introduces provider accounts, webhook verification, refunds, tax and consumer-protection obligations, secrets management, and payment-specific testing. Those are not necessary to demonstrate campaign lifecycle and sponsored placement.

The work is moderate rather than trivial. Upload handling, access control across two account roles, mixed organic/sponsored feed presentation, and the meaning of campaign budget need deliberate design and tests. The proposed MVP remains suitable for a student project by limiting each campaign to one creative, using chronological feeds, and avoiding real money and targeting.

## Recommended Technology Stack

- **Language and web framework:** Python with a currently supported Django release. Django's built-in authentication, sessions, ORM, migrations, forms, CSRF protection, template escaping, and admin site cover most MVP needs.
- **Frontend:** Django templates, accessible HTML, and a small amount of CSS. Start without a separate React/Vue SPA or API. Add HTMX only if a specific interaction benefits from it; it is not required for the MVP.
- **Database:** SQLite is adequate for local development and a small, single-process demonstration. Prefer PostgreSQL when the target CodeRange environment supports it, particularly for deployment and concurrent writes. Keep the data model portable through Django migrations and ORM usage.
- **Images:** Django's storage interface with local media storage for development. Use persistent object storage (for example, an S3-compatible service) if deployment disks are ephemeral or uploads need to scale. Pillow can decode and validate raster images. Do not store image bytes in database rows.
- **Static files:** Keep CSS and other application static assets separate from uploaded media. Use the deployment platform's supported static-file setup rather than treating user uploads as static assets.
- **Testing:** Django's test framework is sufficient initially. Add `pytest`/`pytest-django` only if the team prefers them or the project already uses them.
- **Configuration:** Read `SECRET_KEY`, database configuration, storage credentials, and debug settings from environment variables. The web process should bind to port `5001` in CodeRange unless the deployment contract says otherwise.

This stack keeps deployment and the development feedback loop simple. A JavaScript SPA, task queue, cache, and microservices would add operational work without being needed to meet the stated requirements.

## Project Architecture

Use one Django project and a small number of domain applications. A reasonable starting boundary is:

- `accounts`: custom user model, profile, registration/login/logout, and role checks.
- `social`: follow relationships, posts/reposts, profile timelines, and the home feed.
- `advertising`: campaigns, simulated purchase state, eligibility, and sponsored feed entries.
- Project configuration: settings, URL routing, templates, storage configuration, and deployment entry point.

Keep view functions/classes thin. Put cross-model operations that need authorization or multiple writes (for example, creating a repost or purchasing a campaign) in a small service/form layer. Use model/database constraints for invariants that must survive concurrent requests. Use Django admin for project staff to inspect accounts/campaigns and, if desired, approve submitted campaigns.

Do not introduce a separate API/backend/frontend architecture for the MVP. Add a service boundary around feed and ad selection so those policies can be tested and changed without making templates responsible for data rules.

## Data Model and Relationships

The following is a suggested relational model, not an implementation mandate.

### Users and Profiles

- **User:** A custom Django user based on `AbstractUser`, configured before the first database migration. Store a role such as `member` or `campaign_manager`; Django's `is_staff`/permissions remain separate for trusted project operators.
- **Profile:** A one-to-one relation to the user for public fields such as display name, biography, and optional avatar. Keep authentication credentials and role authorization on the user, not in profile-editable fields.

Use the custom user model from the beginning. Changing the user model after other tables and migrations exist is disproportionately difficult.

### Follows

- **Follow:** `follower` and `followed` are both foreign keys to User, with a creation timestamp.
- Add a unique constraint on `(follower, followed)` to prevent duplicate follows and an index suitable for looking up the accounts a user follows.
- Reject self-following in application validation and, where practical, a database constraint.
- Following is directional: A following B does not imply B follows A. Unfollowing deletes the relationship; it does not delete either account or their content.

### Posts and Reposts

- **Post:** Author foreign key, optional text body, optional image, creation timestamp, and an optional self-referencing `repost_of` foreign key. A normal post has no `repost_of`; a repost points to the original post and does not copy its body or image. A repost can optionally have commentary.
- Require a normal post to have text, an image, or both. Validate this in the form/service and enforce a database check where supported. A repost should not duplicate the original image or content.
- A conditional uniqueness rule on `(author, repost_of)` can limit a user to one repost of a given post if that is the chosen behavior. Reposts can instead be repeatable if product requirements call for it.
- Deleting or hiding an original post needs an explicit policy for its reposts. For a simple project, retain the reference and render a clear “original post unavailable” state rather than copying deleted content.

Using a self-reference keeps the feed query in one timeline table, which is convenient for a small MVP. If reposts later acquire substantially different metadata or lifecycle, split them into their own model and adapt feed queries deliberately.

### Campaigns and Purchases

- **Campaign:** Owner foreign key to a campaign-manager user; campaign name; ad headline/body; one optional image; entered budget in integer minor currency units plus an explicit currency; start/end timestamps; creation timestamp; moderation/delivery status; and payment/simulation status.
- Store monetary amounts as integers in the smallest currency unit (for example cents), not floating-point values. Validate that the amount is positive and end time follows start time.
- Separate campaign lifecycle from payment state. A campaign might be `draft`, `pending_review`, `active`, `paused`, or `completed`; its simulated purchase state should separately indicate `unpaid` or `simulated_paid`. Eligibility should require the required approval and a successful simulated purchase.
- **Impression (optional MVP model):** campaign, user (nullable if anonymous browsing is later supported), and timestamp. Add only if the project needs to demonstrate delivery counts or enforce an impression budget. Do not claim that an impression is a billable event unless pricing and accounting rules are defined.

Campaign creative and delivery state should not be stored as a normal `Post`. This preserves separate ownership, permissions, lifecycle, and payment semantics, and makes it harder to accidentally display an advertisement as user-authored content.

## Authentication and User Roles

Use Django's password hashing, session authentication, login/logout views, CSRF middleware, and password validation. Do not implement password storage or token cryptography manually.

The role check must be enforced on the server for every campaign operation. Hiding campaign controls in templates is not authorization. Campaign-manager users may create, edit, pause, and view only campaigns they own; regular users cannot call those operations by constructing a URL or request directly. Staff operations should use staff permissions, not the public campaign-manager role.

Do not let a user promote themselves by submitting a `role` value in a registration or profile form. Recommended options are staff-created campaign-manager accounts or a manager application that remains a regular account until staff approval. If self-service manager registration is desired for a classroom demo, clearly treat it as a product simplification and still assign the role only through a trusted, server-side flow.

## Following Behavior

Following creates one directed Follow row. Unfollowing removes that row and should immediately exclude that account's future content from the follower's home feed. Existing posts and account data remain intact. The MVP can show follower/following counts computed from relationship rows; cached counts are unnecessary at this scale.

Assume profiles/posts are public within the application unless privacy requirements are added. Private accounts, follow requests, blocks, mutes, and protected-post visibility would change both the model and feed authorization and should not be implied by this design.

## User Feed

For a small MVP, generate the feed on request from posts authored by the current user and accounts they follow, ordered newest first. Include repost records as timeline entries authored by the reposter, displaying the reposter and the referenced original content. The recommended default is that a followed user's repost is visible even when the viewer does not follow the original author; the original post's visibility/deletion rules still apply.

Paginate the feed and select related users/posts in the query to avoid unbounded responses and avoid one database query per card. A simple chronological feed is explainable and testable. Do not start with ranking, machine learning, or per-user feed fan-out. If query volume later becomes a real bottleneck, measure it first; a materialized feed or background fan-out is a later architecture decision with consistency and deletion tradeoffs.

Image posts and reposts are rendered from the same user-post domain. Sponsored content is selected separately and then inserted into the response; it is never included by pretending a campaign is a user's post.

## Ad Campaign Lifecycle and Feed Placement

Campaign creation should validate ownership, creative fields, image content, budget, and schedule. A recommended lifecycle is:

1. Manager saves a draft campaign.
2. Manager submits/purchases it through the simulated flow.
3. The campaign becomes eligible only after its simulated purchase is confirmed, any required staff review is approved, and its active time window has started.
4. It stops being eligible when paused, rejected, out of time, or completed.

Use a distinct feed-item representation for sponsored content, with a visible text label such as **Sponsored** and an advertiser/campaign identity. Do not rely on color alone. Keep ad markup and campaign links separate from normal post actions such as reposting.

For the MVP, query eligible campaigns at feed-render time and insert one after a small fixed number of organic entries (for example, one sponsored item after every five organic items when eligible campaigns exist). Use a simple rotation or deterministic selection to avoid showing the same campaign repeatedly on every request. Do not add demographic/behavioral targeting. If impressions are recorded, use them for demo reporting or rotation only unless the project explicitly defines a billing rule. Handle the no-eligible-ad case by showing an all-organic feed.

Ad insertion should be tested independently from organic feed retrieval. It must never bypass follow filtering, change who authored an organic item, or remove the sponsored label.

## Payment Recommendation

Use a simulated payment system for this project. “Purchase” should be a clearly labeled demo action that records the campaign's requested amount and sets a simulated-paid state; it must not ask for card numbers, bank information, or real payment credentials. Make the UI and documentation explicit that no money moves.

For the MVP, treat budget as a recorded demo campaign amount, not as a real spend ledger. If the project later needs budget depletion, first agree on a pricing rule (such as a fixed demo charge per impression), currency, rounding, refunds, and idempotency, then record delivery events and spend transactionally. Never imply that a manager is buying guaranteed reach when the system has no defined delivery/pricing model.

Real payment integration is a separate future project requiring a payment provider, server-side webhook verification, idempotency, secrets and environment configuration, test-mode coverage, and review of applicable legal/compliance duties. It is not recommended for this student MVP.

## Image and File Storage

Use the framework's storage API and keep media files out of the relational database and source-control repository. For development, save to a local media directory that is not confused with static assets. Verify deployment storage is persistent before relying on local disk; otherwise use configured object storage.

Treat every upload as untrusted input. Enforce a small maximum size and allowed raster formats, inspect/decode the actual file rather than trusting its extension or browser-supplied content type, and generate storage names rather than using user-provided paths. Reject SVG for the initial release unless it is safely sanitized. Consider stripping image metadata. Ensure failed validation does not leave orphaned files, and avoid exposing local filesystem paths in responses.

The study assumes images are public along with the associated public post/campaign. If private accounts or private media are required, direct public media URLs are insufficient and access-controlled delivery is needed.

## Security and Abuse Considerations

- Use Django's password, session, CSRF, template escaping, and ORM protections; keep production debug mode disabled and use HTTPS with secure cookies where deployment supports it.
- Check authentication, role, and object ownership for every mutation and campaign read/update. Test direct URL access as the wrong role and as a different owner.
- Keep secrets out of Git-tracked files. Use environment configuration and rotate any credential that is accidentally exposed.
- Validate uploads by decoded content, dimensions/size, and allowlist; generate file names and use a storage backend with safe URL/path handling.
- Add reasonable rate limits or throttling for login attempts, registrations, posting, following, and simulated purchase endpoints if the app is accessible beyond a trusted classroom network.
- Consider spam, harassment, impersonation, malicious ad creative, and reporting/moderation. At minimum, give staff a way to deactivate accounts or reject/pause campaigns. A public service would need a substantially more complete moderation, privacy, data-retention, and legal review.
- Do not collect or retain payment-card data in the simulated purchase flow.
- Avoid detailed behavioral ad targeting in the MVP. Collect only the data needed to demonstrate the features.

## Assumptions and Open Product Questions

This study uses the following defaults because the request does not specify them:

- Profiles and posts are public to logged-in application users; private accounts and blocks are out of MVP scope.
- The home feed includes the viewer's own posts plus followed users' posts, with reposts attributed to the person who reposted them.
- A followed user's repost is visible even if the viewer does not follow the original author.
- One image per post and one image/creative per campaign is enough initially; text-only posts are allowed.
- Campaign-manager status is trusted and should require staff approval or staff assignment.
- Campaigns need a simulated purchase before delivery. Staff review before activation is recommended to reduce abusive or unsafe ad content.
- Campaign budget is a simulated purchase amount and is not depleted per impression in the MVP.
- Feed ordering is chronological, with simple periodic sponsored insertion and no personalization.
- The target runtime should use CodeRange port `5001`, as specified in the project instructions.

Confirm or revise these before planning, especially:

- Should managers be staff-approved, or can anyone register as a campaign manager?
- Are posts/accounts public, and may logged-out visitors view them?
- Should reposts be repeatable, optionally commented on, or limited to one per user per original post?
- Is staff approval required for campaigns and their images before delivery?
- What does the campaign budget mean in the demo (purchase amount only, fixed ad package, or simulated spend per impression)?
- Which currency, image formats, upload limits, and campaign duration limits should be used?

## Risks and Constraints

- **Workspace/repository state:** The configured project directory currently has only `AGENTS.md`; no app code, tests, requirements, or Git repository are present. Existing architecture and available deployment services cannot be verified. The study is a proposal, not an audit of working code.
- **Git workflow blocker:** `git status` reports that this directory is not a Git repository. The required study commit cannot be made without repository metadata. Initializing Git would be a separate repository-level change and has not been done.
- **Role escalation:** A self-service role field can grant ad privileges unless assignment is controlled server-side.
- **Misleading ad budget:** Recording a budget without a defined billing/delivery model can misrepresent what is being purchased. Keep the simulation conspicuous and describe budget semantics accurately.
- **Upload abuse and storage:** Unvalidated images can exhaust storage or exploit decoders; ephemeral deployment storage can silently lose uploads.
- **Feed edge cases:** Unfollowing, repost visibility, deleted originals, pagination, and ad insertion can yield privacy or ordering bugs if left unspecified.
- **Moderation and public deployment:** A user-generated social app and user-submitted ads expose the project to abuse and content-safety obligations that are not solved by the core feature implementation.
- **Deployment support:** PostgreSQL, persistent media storage, environment variables, HTTPS, and port binding must be confirmed in CodeRange before deployment architecture is finalized.

The design is appropriate for a classroom-scale, single web process. It is not a production social network architecture and should not be represented as one.

## Testing Approach

Use automated tests at model/service and HTTP permission boundaries, plus a small manual browser walkthrough.

- **Model constraints:** duplicate follows rejected; self-follow rejected; invalid empty normal post rejected; post/repost relationship valid; positive budget and valid campaign schedule required; status/payment state combinations cannot accidentally become eligible.
- **Authentication and roles:** anonymous users are redirected or denied as appropriate; regular members cannot manage campaigns; campaign managers cannot view or alter another manager's campaign; profile edits cannot change role; staff-only moderation is protected.
- **Following:** follow creates one relationship, repeated follow is safe, unfollow removes it, and self-follow is refused.
- **Feed:** includes own and followed accounts' posts, excludes unrelated accounts, updates after unfollow, orders newest first, paginates, shows repost actor and original, and handles deleted/unavailable originals without copying content.
- **Uploads:** accept allowed valid images, reject oversized or malformed/disallowed data regardless of claimed extension/type, and do not expose unsafe filesystem paths.
- **Campaigns/purchases:** ownership and date/status/approval/payment gates are enforced; simulated purchase is idempotent and never accepts card data; paused, unpaid, rejected, future, and expired campaigns are not delivered.
- **Sponsored feed:** eligible campaigns are inserted at the defined cadence, ineligible campaigns are not, empty inventory leaves the organic feed intact, sponsored entries are visibly labeled, and ad records never appear as organic posts.
- **End-to-end/manual:** register and log in as both roles, edit profile, post text/image, follow/unfollow, inspect a feed, repost, create and simulate-purchase a campaign, then verify its scheduled sponsored placement and manager/staff controls.

Prefer deterministic test time and campaign selection so tests do not depend on wall-clock timing or random ad choices. Test database behavior with the same database engine intended for deployment when feasible, since constraints can differ between SQLite and PostgreSQL.

## Recommended MVP Scope

Include:

- Registration, login, logout, one profile per account, and server-enforced member/campaign-manager roles.
- Text-only and one-image user posts.
- Follow and unfollow with unique directed relationships.
- A paginated chronological home feed containing own and followed users' posts.
- Reposts that reference rather than duplicate the original, with a clear reposter attribution.
- Campaign-manager campaign creation/editing with one creative, budget, start/end dates, and a simulated purchase action.
- A simple staff review/approval path or explicit staff-only campaign activation.
- Active, paid-simulated, in-window campaign insertion at a simple fixed cadence, visibly marked Sponsored.
- Safe image validation, basic ownership/role tests, and deployment configuration for CodeRange port `5001`.

Defer:

- Real payment provider, card collection, refunds, tax calculations, and spend settlement.
- Algorithmic feeds, per-user feed fan-out, behavioral or demographic ad targeting, bidding, and advanced campaign analytics.
- Likes, comments, direct messages, notifications, search, hashtags, recommendations, and real-time updates.
- Private accounts, follow approvals, blocks/mutes, detailed reporting workflows, and sophisticated moderation queues unless needed for the intended audience.
- Multiple creatives per campaign, video, image transformations/CDN, and large-scale storage/processing pipelines.
- Microservices, a separate SPA/API, task queues, caches, and event streaming before measurements demonstrate a need.

This scope demonstrates the requested social and advertising concepts while keeping payment, feed delivery, and operational complexity controlled. Before moving to a plan, resolve the open product decisions and confirm the actual repository root/Git setup.
