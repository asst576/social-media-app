# Advertising Demo

## Campaign Lifecycle

Campaign managers are provisioned by staff; public signup cannot assign the manager role. A manager creates a draft with a name, headline/body, one optional image, USD budget, and start/end datetimes. Managers can edit drafts or rejected campaigns and submit them for review.

Staff approve or reject pending campaigns with Django admin actions. Staff can pause/resume approved campaigns. After approval, the manager may simulate a purchase; this is available only before the campaign end time and repeated submissions are idempotent.

## Feed Eligibility

A campaign is eligible only when it is approved, simulated-paid, and `starts_at <= now < ends_at`. Campaign rows remain separate from organic `social.Post` rows. The feed inserts one eligible campaign after every five organic entries and rotates selections in the member's session. Sponsored items show a visible label and advertiser identity.

No real money moves. The stored budget is a simulated purchase amount and is not depleted per impression. There is no behavioral targeting or advanced delivery analytics.
