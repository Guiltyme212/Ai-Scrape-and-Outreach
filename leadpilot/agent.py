"""LeadPilot Agent — orchestrates the full pipeline."""

import logging

from leadpilot.config import settings
from leadpilot.sheets import get_leads, update_score, update_result
from leadpilot.scorer import score_website
from leadpilot.generator import generate_preview
from leadpilot.deployer import deploy_to_netlify
from leadpilot.emailer import draft_email

log = logging.getLogger("leadpilot")


def run_pipeline(limit: int | None = None, dry_run: bool = False):
    """Process leads from the Google Sheet.

    Args:
        limit: Max number of leads to process. None = all.
        dry_run: If True, only score websites — no preview/deploy/email.
    """
    log.info("Starting LeadPilot pipeline...")
    leads = get_leads()
    log.info(f"Found {len(leads)} leads in sheet")

    # Filter to unprocessed leads (no score yet)
    unprocessed = [lead for lead in leads if not lead["score"]]
    log.info(f"{len(unprocessed)} unprocessed leads")

    if limit:
        unprocessed = unprocessed[:limit]
        log.info(f"Processing {len(unprocessed)} leads (limit={limit})")

    processed = 0
    errors = 0

    for lead in unprocessed:
        row = lead["row_index"]
        name = lead["business_name"] or "Unknown"
        url = lead["website"]

        if not url:
            log.warning(f"Row {row}: No website URL, skipping")
            continue

        log.info(f"\n{'='*60}")
        log.info(f"Processing: {name} ({url})")
        log.info(f"{'='*60}")

        try:
            # Step 1: Score the website
            log.info(f"  [1/4] Scoring website...")
            result = score_website(url)
            score = result["score"]
            issues = result.get("issues", [])
            extracted = result.get("extracted", {})

            log.info(f"  Score: {score}/100")
            log.info(f"  Issues: {', '.join(issues[:3])}")

            # Write score to sheet
            update_score(row, score)
            log.info(f"  Score written to sheet")

            if dry_run:
                log.info(f"  [DRY RUN] Skipping preview/deploy/email")
                processed += 1
                continue

            # Step 2: Generate preview (only if score is below threshold)
            if score >= settings.score_threshold:
                log.info(f"  Score {score} >= {settings.score_threshold} — site is good enough, skipping preview")
                processed += 1
                continue

            log.info(f"  [2/4] Generating preview site...")
            business_name = extracted.get("business_name") or name
            business_type = extracted.get("business_type") or ""
            services = extracted.get("services") or []
            contact_info = {
                "phone": extracted.get("phone", ""),
                "address": extracted.get("address", ""),
                "email": lead.get("email", ""),
            }

            html = generate_preview(
                business_name=business_name,
                business_type=business_type,
                description=lead["description"],
                services=services,
                contact_info=contact_info,
                issues=issues,
            )
            log.info(f"  Preview generated ({len(html)} chars)")

            # Step 3: Deploy to Netlify
            log.info(f"  [3/4] Deploying to Netlify...")
            preview_url = deploy_to_netlify(html, business_name)
            log.info(f"  Live at: {preview_url}")

            # Step 4: Draft email
            log.info(f"  [4/4] Drafting email...")
            email = draft_email(
                business_name=business_name,
                business_type=business_type,
                score=score,
                issues=issues,
                preview_url=preview_url,
            )
            log.info(f"  Subject: {email['subject']}")

            # Write results to sheet
            update_result(row, preview_url, email["subject"], email["body"])
            log.info(f"  Results written to sheet")

            processed += 1

        except Exception as e:
            log.error(f"  ERROR processing {name}: {e}")
            errors += 1
            continue

    log.info(f"\n{'='*60}")
    log.info(f"Pipeline complete: {processed} processed, {errors} errors")
    log.info(f"{'='*60}")
