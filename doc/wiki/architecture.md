# Application Architecture

## Runtime and Django Apps

Commonplace is a Django monolith using Django Templates, SQLite, built-in authentication, and Pillow. The `config` package owns project settings and root URL routing. Domain code is split into:

- `accounts`: custom user, profile, registration, login/logout, and profile views.
- `social`: follows, posts/reposts, member directory, and chronological feed.
- `advertising`: campaigns, delivery eligibility, simulated purchase, and staff moderation.

Views use Django forms and the ORM. Templates escape user-provided text. The app has no separate SPA or API service.

## Accounts and Profiles

`accounts.User` extends `AbstractUser` and stores a server-managed `role` of `member` or `campaign_manager`. Django's `is_staff` and superuser permissions are separate. Public signup always creates a regular member. Trusted staff assign campaign-manager status through Django admin.

`accounts.Profile` is one-to-one with User and stores a display name and biography. A post-save signal creates profiles for new users.

## Social Data

- `social.Follow` is a directed follower-to-followed relationship. Database constraints prevent duplicate pairs and self-following.
- `social.Post` stores authored text and/or one image. A repost is a Post row whose `repost_of` points to the original; content is not copied. One user may repost an original once, and self-reposts/repost chains are rejected.
- `repost_of` uses `on_delete=PROTECT`, so an original cannot be deleted while reposts reference it.

The authenticated people directory is a username-ordered, paginated list without search. The feed contains the signed-in member's posts and posts/reposts by accounts they follow, ordered newest-first and paginated at ten organic entries.

## Advertising Data and Delivery

`advertising.Campaign` is separate from user posts. It belongs to a campaign-manager and stores ad text/image, a USD amount in integer cents, a schedule, review status, and simulated-payment state. Staff review submitted campaigns in Django admin. Delivery requires approval, simulated purchase, and a current time within the campaign schedule. The feed inserts one eligible sponsored item after every five organic items and labels it `Sponsored`.

Campaign budget is demo purchase metadata only. No payment provider is called and the amount is not depleted by impressions.

## Uploaded Media

Posts and campaigns each support one optional image. Upload validation checks decoded JPEG/PNG/WebP content, the 5 MiB file-size limit, and the configured pixel limit. Files use generated names and are stored outside database rows. Local media serving is enabled in debug mode only.
