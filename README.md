# Local Affiliate Content Operations System

This is a real local, human-reviewed operating system for affiliate and faceless-content production. It is intentionally **not an auto-publisher**. It stores products, evidence, content drafts, risk flags, approval decisions, and approved export packages in SQLite.

## What is implemented

- Product and offer library with URLs, restrictions, notes, and verified facts.
- Evidence register so claims can be tied to a source and marked verified.
- Content queue for TikTok, Instagram Reels, YouTube Shorts, Pinterest, blog, or any custom channel.
- Reusable script/caption generator with disclosure included by default.
- Risk scanner for health, finance, legal, religion, disclosure, and product-restriction issues.
- Human approval gate. Drafts with risk flags cannot be approved unless an explicit override and reviewer note are supplied.
- Markdown export packages containing hook, script, caption, CTA, and disclosure.
- Basic operational report.

## Quick start

```bash
cd /home/ubuntu/affiliate_ops
python3 affiliate_ops.py add-product --name "Example product" --category "category" --url "https://example.com" --affiliate-url "https://example.com/?ref=YOUR_ID"
python3 affiliate_ops.py list products
python3 affiliate_ops.py add-evidence --product-id PRODUCT_ID --source-url "https://example.com/specs" --claim "The official page states X" --verified
python3 affiliate_ops.py create-content --product-id PRODUCT_ID --channel tiktok --angle "buyer checklist"
python3 affiliate_ops.py list content
python3 affiliate_ops.py approve --content-id CONTENT_ID --reviewer "your name" --decision approved --notes "Checked source, disclosure, and current terms."
python3 affiliate_ops.py export
python3 affiliate_ops.py report
```

## Operating rules

1. Add a product before creating content.
2. Add source-backed evidence for every factual claim you want to present.
3. Treat generated copy as a draft, not proof of product performance.
4. Review all risk flags manually, especially health, finance, legal, religious, or sensitive claims.
5. Confirm affiliate disclosure, current price, availability, terms, and link destination before approval.
6. Export only approved content. Publishing remains a separate manual action.

## Configuration

Edit `config.json` to set the brand name, niche, default channels, disclosure, CTA, and output directory. The initial configuration leaves niche blank deliberately so the system can be reused across categories.

## Scheduling

The current system is safe to run manually. To run the daily operational report, add a local cron entry after confirming the path:

```cron
0 9 * * * cd /home/ubuntu/affiliate_ops && /usr/bin/python3 affiliate_ops.py report >> operations.log 2>&1
```

Do not schedule publishing. Schedule only deterministic maintenance/reporting until a human-review workflow is in place.

## Extension points

The next adapters can be added without changing the database model: product research import, URL/affiliate-link validation, LLM-assisted draft generation, Google Sheets export, cloud backup, and channel-specific formatting. External API keys should be stored outside the repository and never in content records.
