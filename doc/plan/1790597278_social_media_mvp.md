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

- [x] Confirm Python 3.12 and choose Django 5.2.17, which is compatible with it.
- [x] Create the Django project and the `accounts`, `social`, and `advertising` apps; keep the project as one server-rendered monolith.
- [x] Add only Django and Pillow as application dependencies; pin resolved versions in `requirements.txt`.
- [x] Configure SQLite for local development, environment-based `SECRET_KEY` and debug settings, timezone-aware datetimes, static files, and local media storage.
- [x] Configure and document the application launch command for port `5001` in CodeRange. The existing process occupying local port `5001` prevented binding to it during validation.
- [x] Add `.gitignore` entries for the local SQLite database, media uploads, virtual environment, bytecode, and local secrets.
- [x] Create the custom user model before the initial migration and set `AUTH_USER_MODEL` before migrating.
- [x] Add project-level URL routing, a shared base template, navigation, and a small responsive stylesheet.
- [x] Verify the new project starts, run the initial Django system check, and apply migrations.

Likely files: `manage.py`, `requirements.txt`, `.gitignore`, project package (`settings.py`, `urls.py`, `wsgi.py`/`asgi.py`), app packages, `templates/base.html`, and `static/css/site.css`.

### 2. Database Models and Authentication/Roles

- [x] Implement a custom `User` based on Django `AbstractUser` with a server-managed role for regular members and campaign managers; keep `is_staff` separate.
- [x] Implement a one-to-one `Profile` with a display name and short biography; create profiles reliably when users are created.
- [x] Add registration, login, and logout routes/forms using Django authentication, password validation, sessions, CSRF protection, and messages.
- [x] Ensure public signup always creates a regular member; never accept a role or staff flag from submitted profile/signup fields.
- [x] Register users/profiles with Django admin so trusted staff can provision manager accounts.
- [x] Implement an authenticated profile view and a safe profile-edit form that cannot modify account role or authentication fields.
- [x] Add tests for account creation, login/logout, profile creation/editing, and role escalation attempts.

Likely files: `accounts/models.py`, `accounts/forms.py`, `accounts/views.py`, `accounts/urls.py`, `accounts/admin.py`, `accounts/tests.py`, project settings/URLs, and account templates.

### 3. Posts and Image Uploads

- [x] Implement `Post` with an author foreign key, optional text body, optional image, creation time, and optional self-reference to the original post for reposts.
- [x] Enforce the content invariant: an original post must contain text or an image; a repost references an original and does not duplicate its content or image.
- [x] Build a post form supporting text-only, image-only, or text-plus-one-image posts.
- [x] Validate the decoded image format and enforce the configured size limit; generate safe stored names and keep user uploads separate from static assets.
- [x] Add authenticated post creation and profile-timeline behavior. Editing/deletion are omitted from the MVP; original posts referenced by reposts are protected from deletion.
- [x] Add tests for text/image combinations, invalid/malformed uploads, upload limits, author attribution, and unauthorized mutations.

Likely files: `social/models.py`, `social/forms.py`, `social/views.py`, `social/urls.py`, `social/admin.py`, `social/tests.py`, media settings, and social templates.

### 4. Follow and Unfollow

- [x] Implement directional `Follow` rows with follower/followed user references and creation time.
- [x] Add a unique constraint for each follower/followed pair and prevent self-following in the request and model validation.
- [x] Implement authenticated follow/unfollow actions that are safe to repeat and use POST requests with CSRF protection.
- [x] Add a simple paginated authenticated member directory so users can discover profiles to follow without adding search.
- [x] Display basic following/follower counts on authenticated profiles without adding cached counters.
- [x] Add tests for follow creation, duplicate follow, self-follow rejection, unfollow, and access restrictions.

Likely files: `social/models.py`, `social/views.py`, `social/urls.py`, `social/tests.py`, profile templates, and migrations.

### 5. Chronological Feed

- [x] Implement an authenticated home feed containing the current user's posts and posts/reposts authored by accounts the user follows.
- [x] Order organic entries newest-first with a stable tie-breaker and paginate results.
- [x] Use ORM relationships efficiently so rendering a page does not perform a query per item.
- [x] Ensure unfollowing removes that account's entries from subsequent feed requests and unrelated accounts' posts are excluded.
- [x] Render image, text, author, timestamp, and repost attribution with escaped template output.
- [x] Add tests for own posts, followed posts, unrelated posts, chronological ordering, pagination, and feed changes after unfollow.

Likely files: `social/views.py`, `social/urls.py`, feed templates, and `social/tests.py`.

### 6. Reposting/Sharing

- [x] Implement a repost as a new timeline entry that references the original post instead of copying its body/image.
- [x] Keep reposts one-click with no commentary (comments are deferred); only allow sharing an original post in the MVP to avoid nested repost chains.
- [x] Prevent duplicate reposts by the same user for the same original post and prevent reposting one's own post.
- [x] Show both the reposter and original author/content in feeds and profile timelines. `PROTECT` prevents deleting an original while reposts refer to it, so unavailable originals cannot be produced through the MVP.
- [x] Add tests for reference integrity, attribution, duplicate/self repost rules, and feed ordering.

Likely files: social models/forms/views/URLs/admin/tests, migrations, and post/feed templates.

### 7. Advertisement Campaigns and Staff Approval

- [x] Implement a `Campaign` owned by a campaign-manager user, with name, ad text, one optional image, integer minor-unit budget, configured currency, start/end datetimes, moderation status, simulated-payment state, and timestamps.
- [x] Validate positive budget, valid date range, allowed image content/size, and manager ownership.
- [x] Add manager-only campaign list/create/edit/detail views; scope every query and mutation to the current owner's campaigns.
- [x] Exclude approval and payment fields from manager-editable forms so managers cannot self-approve or set payment state directly.
- [x] Add staff review through Django admin approve/reject actions; record reviewer and review time. Staff can also pause/resume approved campaigns.
- [x] Ensure staff approval is distinct from simulated purchase and neither action alone makes a campaign deliverable.
- [x] Add tests for role enforcement, ownership isolation, staff approval permissions, campaign validation, and status transitions.

Likely files: `advertising/models.py`, `advertising/forms.py`, `advertising/views.py`, `advertising/urls.py`, `advertising/admin.py`, `advertising/tests.py`, and campaign templates.

### 8. Simulated Purchase Flow

- [x] Add a manager-only POST action to simulate purchasing an owned campaign; make it idempotent and require approval first.
- [x] Record only a simulated-paid state and the configured demo amount/currency; do not collect card/bank data or call a payment provider.
- [x] Display a clear notice that the purchase is a demo and no money is transferred.
- [x] Keep campaign budget as recorded demo purchase value; do not decrement it based on feed impressions.
- [x] Add tests for successful simulation, repeated submissions, ownership checks, invalid states, and absence of payment credential fields.

Likely files: advertising models/forms/views/URLs/tests and campaign templates.

### 9. Sponsored Feed Insertion

- [x] Define campaign eligibility in one testable service: approved, simulated-paid, not rejected/paused, and current time within the campaign window.
- [x] Fetch eligible campaigns separately from organic posts; never represent a campaign as a user `Post` or include it in organic author/follow queries.
- [x] Insert one eligible campaign after every five organic entries using per-session rotation; gracefully return an all-organic feed when no eligible campaigns exist.
- [x] Render campaigns with a persistent, accessible `Sponsored` label and advertiser identity; do not rely on color alone.
- [x] Keep ad controls/links distinct from repost actions and do not add user-level behavioral targeting.
- [x] Add tests for each eligibility gate, schedule boundaries, insertion cadence, no-inventory behavior, rotation, and the visible sponsored label.

Likely files: `advertising/services.py`, social feed view/service and templates, `advertising/tests.py`, and integration tests.

### 10. Testing, Validation, and Hardening

- [x] Complete model and request tests across accounts, permissions, follows, posts/images, feeds, reposts, campaign approval, simulated purchasing, and ad insertion.
- [x] Use generated image fixtures and temporary media storage in tests; clean up uploaded files after each test.
- [x] Verify state-changing endpoints require POST and CSRF protection.
- [x] Verify campaign ownership and role checks are enforced server-side, including direct requests as a regular user and as another campaign manager.
- [x] Run `python manage.py check` and `python manage.py makemigrations --check --dry-run`.
- [x] Run migrations against SQLite and the complete Django test suite.
- [x] Start the application on temporary local port `5002` and verify the login route returns HTTP 200; feature journeys are exercised by the automated request tests.
- [x] Run the app on port `5001` and exercise signup, logout, and login through CodeRange host/prefix requests; feature-specific social and campaign journeys are covered by automated request tests.
- [x] Before commit, inspect the staged file list and verify no secrets, local database, uploaded media, or generated files are staged for Git.

### 11. Documentation Updates

- [x] Update `README.md` with supported Python/Django setup, dependency installation, migrations, test command, local run command/port, and media upload configuration.
- [x] Document how staff provisions campaign managers and approves campaigns.
- [x] Clearly document that campaign purchase is simulated, no money moves, the selected budget currency is a demo setting, and impressions do not consume budget.
- [x] Document the implemented MVP limitations and deferred features without claiming deferred features exist.
- [x] Record living wiki/footguns documentation for the explicit later `sync docs` workflow in `TODO.md`; do not perform that phase automatically during execution or rendezvous.

Likely files: `README.md`; later documentation sync: `doc/wiki/` and, if needed, `doc/wiki/footguns/`.

## Completion Criteria

- [x] The application runs locally with SQLite using the specified stack and is configured/documented to launch on CodeRange port `5001`.
- [x] A regular user can register, log in/out, edit a profile, create text/image posts, follow/unfollow users, view the chronological feed, and repost original posts.
- [x] A staff-provisioned campaign manager can create a campaign with text, one image, budget, and date range, then simulate purchase without real payment credentials.
- [x] Staff can approve/reject campaigns; only approved, simulated-paid campaigns in their date window appear in feeds.
- [x] Every inserted ad is visibly labeled Sponsored and remains distinct from normal user content.
- [x] Automated tests cover feature behavior, upload validation, role/ownership boundaries, feed filtering, and ad eligibility/insertion.
- [x] Setup and demo behavior are documented, and execution stops for the user to invoke `rendezvous`.
- [x] Verify startup on port `5001` using the CodeRange host and proxy-shaped paths. The public HTTPS edge is not reachable from this workspace, but the forwarded host/path requests return successfully.

## Execution Notes

- Before executing, check Git status, review the repository, and create a separate feature branch as required by `AGENTS.md`.
- Keep the initial migration for the custom user model in the first migration cycle.
- Prefer Django built-ins and the listed dependencies; do not add a SPA, payment SDK, task queue, cache, or analytics platform.
- Update completed checklist items to `[x]` during execution. Do not merge the feature branch during execute-plan; wait for the explicit `rendezvous` instruction.
