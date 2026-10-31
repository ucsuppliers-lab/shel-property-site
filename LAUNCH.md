# Going live: switches and steps

Nothing here happens automatically. Each step needs Eli's yes.

1. **Company details** go into the footer small print (`i18n.py`, `f_legal`) and the privacy notice (`templates/info_privacy.html`).
2. **Enquiry forms**: in Netlify, Site configuration → Environment variables, add `SHEL_FORMS = 1`, and turn on Forms → form detection.
   Forms post to Netlify Forms; set an email notification to adam@shelproperty.com. Form submissions are free on the credit plans (Netlify, 14 Apr 2026).
3. **Search engines**: on the public site only, add `SHEL_LIVE = 1`. This switches pages to `index, follow`, opens robots.txt and
   points it at sitemap.xml. Remove the `X-Robots-Tag = "noindex, nofollow"` header from `netlify.toml` at the same time.
4. **Domain**: at GoDaddy, A `@` → 75.2.60.5 and CNAME `www` → the Netlify site; keep the MX/TXT email records.
5. After launch, submit https://shelproperty.com/sitemap.xml in Google Search Console and Bing Webmaster Tools (both free).

Staging (`shel-property-staging`) never gets SHEL_LIVE, and it shows hidden drafts.
Netlify free plan: 300 credits a month. Each production deploy costs 15 credits, and bandwidth costs 20 credits per GB, so batch changes.
