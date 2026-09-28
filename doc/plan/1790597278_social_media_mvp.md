# 1790597278 Social Media MVP Implementation Plan

## Source and Scope

Based on `doc/study/1790595150_social_media_application_feasibility.md` and the user's MVP requirements. Implement a minimal Django application using Python, Django Templates, HTML/CSS, SQLite, built-in authentication, Pillow, and Git. Do not add real payments or any deferred social/advertising features.

## OPEN QUESTIONS

These decisions have recommended defaults so implementation can proceed without blocking. Confirm or revise them before execution if they are not acceptable:

- What currency should the demo campaign budget display? **Default:** use a single configured display currency (USD) and state that both currency and purchase are simulated; collect no financial credentials.
- How are campaign-manager accounts provisioned? **Default:** regular users register through the public signup form; trusted staff assign the campaign-manager role through Django admin.
- Who can view the application feed? **Default:** require login for the home feed; profiles/posts are visible to authenticated users. Do not implement private accounts.
- When is a campaign deliverable? **Default:** only after staff approval and simulated purchase, and only inside its start/end window. The budget is recorded as a simulated purchase amount and is not consumed per impression.
- How often are ads inserted? **Default:** insert one eligible sponsored campaign after every five organic feed entries, with a simple deterministic rotation and no behavioral targeting.
- What upload limits should be enforced? **Default:** allow one decoded JPEG, PNG, or WebP image up to 5 MiB per post/campaign; keep this limit configurable and validate actual image data.

## Implementation Checklist

### 1. Project Setup

- [ ] Confirm the Python version available in the target environment and choose a currently supported Django version compatible with it.
- [ ] Create the Django project and the `accounts`, `social`, and `advertising` apps; keep the project as one server-rendered monolith.
- [ ] Add only Django and Pillow as application dependencies; record resolved compatible versions in `requirements.txt`.
- [ ] Configure SQLite for local development, environment-based `SECRET_KEY` and debug settings, timezone-aware datetimes, static files, and local media storage.
- [ ] Configure the application to run on port `5001` in CodeRange.
- [ ] Add `.gitignore` entries for the local SQLite database, media uploads, virtual environment, bytecode, and local secrets.
- [ ] Create the custom user model before the initial migration and set `AUTH_USER_MODEL` before migrating.
- [ ] Add project-level URL routing, a shared base template, navigation, and a small responsive stylesheet.
- [ ] Verify the new project starts and run the initial Django system check and migrations.

Likely files: `manage.py`, `requirements.txt`, `.gitignore`, project package (`settings.py`, `urls.py`, `wsgi.py`/`asgi.py`), app packages, `templates/base.html`, and `static/css/site.css`.

### 2. Database Models and Authentication/Roles

- [ ] Implement a custom `User` based on Django `AbstractUser` with a server-managed role for regular members and campaign managers; keep `is_staff` separate.
- [ ] Implement a one-to-one `Profile` with a display name and short biography; create profiles reliably when users are created.
- [ ] Add registration, login, and logout routes/forms using Django authentication, password validation, sessions, CSRF protection, and messages.
- [ ] Ensure public signup always creates a regular member; never accept a role or staff flag from submitted profile/signup fields.
- [ ] Register users/profiles with Django admin so trusted staff can provision manager accounts.
- [ ] Implement an authenticated profile view and a safe profile-edit form that cannot modify account role or authentication fields.
- [ ] Add tests for account creation, login/logout, profile creation/editing, and role escalation attempts.

Likely files: `accounts/models.py`, `accounts/forms.py`, `accounts/views.py`, `accounts/urls.py`, `accounts/admin.py`, `accounts/tests.py`, project settings/URLs, and account templates.

### 3. Posts and Image Uploads

- [ ] Implement `Post` with an author foreign key, optional text body, optional image, creation time, and optional self-reference to the original post for reposts.
- [ ] Enforce the content invariant: an original post must contain text or an image; a repost references an original and does not duplicate its content or image.
- [ ] Build a post form supporting text-only, image-only, or text-plus-one-image posts.
- [ ] Validate the decoded image format and enforce the configured size limit; generate safe stored names and keep user uploads separate from static assets.
- [ ] Add authenticated create-post and post-detail/profile-timeline behavior; ensure only the author can edit/delete if editing/deletion is included (otherwise omit those actions from the MVP).
- [ ] Add tests for text/image combinations, invalid/malformed uploads, upload limits, author attribution, and unauthorized mutations.

Likely files: `social/models.py`, `social/forms.py`, `social/views.py`, `social/urls.py`, `social/admin.py`, `social/tests.py`, media settings, and social templates.

### 4. Follow and Unfollow

- [ ] Implement directional `Follow` rows with follower/followed user references and creation time.
- [ ] Add a unique constraint for each follower/followed pair and prevent self-following in the request and model validation.
- [ ] Implement authenticated follow/unfollow actions that are safe to repeat and use POST requests with CSRF protection.
- [ ] Display basic following/follower lists or counts on authenticated profiles without adding cached counters.
- [ ] Add tests for follow creation, duplicate follow, self-follow rejection, unfollow, and access restrictions.

Likely files: `social/models.py`, `social/views.py`, `social/urls.py`, `social/tests.py`, profile templates, and migrations.

### 5. Chronological Feed

- [ ] Implement an authenticated home feed containing the current user's posts and posts/reposts authored by accounts the user follows.
- [ ] Order organic entries newest-first with a stable tie-breaker and paginate results.
- [ ] Use ORM relationships efficiently so rendering a page does not perform a query per item.
- [ ] Ensure unfollowing removes that account's entries from subsequent feed requests and unrelated accounts' posts are excluded.
- [ ] Render image, text, author, timestamp, and repost attribution with escaped template output.
- [ ] Add tests for own posts, followed posts, unrelated posts, chronological ordering, pagination, and feed changes after unfollow.

Likely files: `social/views.py`, `social/urls.py`, feed templates, and `social/tests.py`.

### 6. Reposting/Sharing

- [ ] Implement a repost as a new timeline entry that references the original post instead of copying its body/image.
- [ ] Keep reposts one-click with no commentary (comments are deferred); only allow sharing an original post in the MVP to avoid nested repost chains.
- [ ] Prevent duplicate reposts by the same user for the same original post and prevent reposting one's own post if that keeps the interaction simpler.
- [ ] Show both the reposter and original author/content in feeds and profile timelines; handle an unavailable/deleted original clearly.
- [ ] Add tests for reference integrity, attribution, duplicate/self repost rules, feed ordering, and missing originals.

Likely files: social models/forms/views/URLs/admin/tests, migrations, and post/feed templates.

### 7. Advertisement Campaigns and Staff Approval

- [ ] Implement a `Campaign` owned by a campaign-manager user, with name, ad text, one optional image, integer minor-unit budget, configured currency, start/end datetimes, moderation status, simulated-payment state, and timestamps.
- [ ] Validate positive budget, valid date range, allowed image content/size, and manager ownership.
- [ ] Add manager-only campaign list/create/edit/detail views; scope every query and mutation to the current owner's campaigns.
- [ ] Exclude approval and payment fields from manager-editable forms so managers cannot self-approve or set payment state directly.
- [ ] Add a simple staff review path through Django admin with approve/reject actions or protected status editing; record reviewer and review time if this can be done without unnecessary complexity.
- [ ] Ensure staff approval is distinct from simulated purchase and neither action alone makes a campaign deliverable.
- [ ] Add tests for role enforcement, ownership isolation, staff approval permissions, campaign validation, and status transitions.

Likely files: `advertising/models.py`, `advertising/forms.py`, `advertising/views.py`, `advertising/urls.py`, `advertising/admin.py`, `advertising/tests.py`, and campaign templates.

### 8. Simulated Purchase Flow

- [ ] Add a manager-only POST action to simulate purchasing an owned campaign; make it idempotent and require valid campaign details.
- [ ] Record only a simulated-paid state and the configured demo amount/currency; do not collect card/bank data or call a payment provider.
- [ ] Display a clear notice that the purchase is a demo and no money is transferred.
- [ ] Keep campaign budget as recorded demo purchase value; do not decrement it based on feed impressions.
- [ ] Add tests for successful simulation, repeated submissions, ownership checks, rejected/invalid campaigns, and absence of payment credential fields.

Likely files: advertising models/forms/views/URLs/tests and campaign templates.

### 9. Sponsored Feed Insertion

- [ ] Define campaign eligibility in one testable service: approved, simulated-paid, not rejected/paused, and current time within the campaign window.
- [ ] Fetch eligible campaigns separately from organic posts; never represent a campaign as a user `Post` or include it in organic author/follow queries.
- [ ] Insert one eligible campaign after every five organic entries using deterministic rotation; gracefully return an all-organic feed when no eligible campaigns exist.
- [ ] Render campaigns with a persistent, accessible `Sponsored` label and advertiser identity; do not rely on color alone.
- [ ] Keep ad controls/links distinct from repost actions and do not add user-level behavioral targeting.
- [ ] Add tests for each eligibility gate, schedule boundaries, insertion cadence, no-inventory behavior, deterministic rotation, and the visible sponsored label.

Likely files: `advertising/services.py`, social feed view/service and templates, `advertising/tests.py`, and integration tests.

### 10. Testing, Validation, and Hardening

- [ ] Complete model and request tests across accounts, permissions, follows, posts/images, feeds, reposts, campaign approval, simulated purchasing, and ad insertion.
- [ ] Use generated in-memory image fixtures and temporary media storage in tests; clean up uploaded files between tests.
- [ ] Verify all state-changing endpoints require POST and CSRF protection.
- [ ] Verify campaign ownership and role checks are enforced server-side, including direct requests as a regular user and as another campaign manager.
- [ ] Run `python manage.py check` and `python manage.py makemigrations --check --dry-run`.
- [ ] Run migrations against SQLite and the complete Django test suite.
- [ ] Run the application on port `5001` and manually exercise signup/login/logout, profile editing, post upload, follow/unfollow, feed, repost, manager campaign creation, staff approval, simulated purchase, and sponsored display.
- [ ] Confirm no secrets, local database, uploaded media, or generated files are staged for Git.

### 11. Documentation Updates

- [ ] Update `README.md` with supported Python/Django setup, dependency installation, migrations, test command, local run command/port, and media upload configuration.
- [ ] Document how staff provisions campaign managers and approves campaigns.
- [ ] Clearly document that campaign purchase is simulated, no money moves, the selected budget currency is a demo setting, and impressions do not consume budget.
- [ ] Document the MVP limitations and deferred features without claiming they are implemented before the work is complete.
- [ ] During the later `sync docs` workflow phase, add or update living pages under `doc/wiki/` and record relevant operational footguns under `doc/wiki/footguns/`; do not perform that workflow phase automatically during execution or rendezvous.

Likely files: `README.md`; later documentation sync: `doc/wiki/` and, if needed, `doc/wiki/footguns/`.

## Completion Criteria

- [ ] The application runs locally with SQLite and on CodeRange port `5001` using the specified stack.
- [ ] A regular user can register, log in/out, edit a profile, create text/image posts, follow/unfollow users, view the chronological feed, and repost original posts.
- [ ] A staff-provisioned campaign manager can create a campaign with text, one image, budget, and date range, then simulate purchase without real payment credentials.
- [ ] Staff can approve/reject campaigns; only approved, simulated-paid campaigns in their date window appear in feeds.
- [ ] Every inserted ad is visibly labeled Sponsored and remains distinct from normal user content.
- [ ] Automated tests cover feature behavior, upload validation, role/ownership boundaries, feed filtering, and ad eligibility/insertion.
- [ ] Setup and demo behavior are documented, and execution stops for the user to invoke `rendezvous`.

## Execution Notes

- Before executing, check Git status, review the repository, and create a separate feature branch as required by `AGENTS.md`.
- Keep the initial migration for the custom user model in the first migration cycle.
- Prefer Django built-ins and the listed dependencies; do not add a SPA, payment SDK, task queue, cache, or analytics platform.
- Update completed checklist items to `[x]` during execution. Do not merge the feature branch during execute-plan; wait for the explicit `rendezvous` instruction.
