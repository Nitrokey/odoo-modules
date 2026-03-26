import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Transfer DHL data from res.company to carrier.account"""
    _logger.info("Starting post-migration: Transferring DHL data to carrier.account")

    env = api.Environment(cr, SUPERUSER_ID, {})

    # Validate prerequisites
    if "carrier.account" not in env:
        return _logger.warning("carrier.account model not found, skipping migration")

    cr.execute(
        "SELECT EXISTS ("
        "SELECT FROM information_schema.tables "
        "WHERE table_name = 'temp_dhl_company_data'"
        ")"
    )
    if not cr.fetchone()[0]:
        return _logger.error("Temporary table 'temp_dhl_company_data' does not exist")

    # Get the DHL delivery carrier(s)
    dhl_carrier = env.ref("delivery_dhl_parcel_de.dhl_parcel_delivery_type", False)
    if not dhl_carrier:
        return _logger.warning("DHL delivery carrier not found, skipping migration")
    _logger.info(f"Found {len(dhl_carrier)} DHL carrier")

    # Get company data
    cr.execute("SELECT * FROM temp_dhl_company_data")
    companies_data = cr.dictfetchall()
    if not companies_data:
        return _logger.info("No company data found in temporary table")

    # Get carrier.account fields
    cr.execute(
        "SELECT column_name "
        "FROM information_schema.columns "
        "WHERE table_name = 'carrier_account'"
    )
    carrier_fields = {row[0] for row in cr.fetchall()}

    field_mapping = [
        "dhl_parcel_de_api_url",
        "dhl_userid",
        "dhl_password",
        "dhl_api_key",
        "dhl_api_secret",
        "dhl_tracking_url",
        "dhl_access_token",
    ]

    success = failed = 0

    for data in companies_data:
        try:
            company_id = data.pop("company_id")

            existing = env.ref("delivery_dhl_parcel_de.dhl_carrier_account")
            if existing and existing.dhl_userid and existing.dhl_password and existing.dhl_api_key:
                _logger.info("Already migrated")
                continue

            account_vals = {
                "company_id": company_id,
                "carrier_id": dhl_carrier.id,
                **{
                    k: v
                    for k, v in data.items()
                    if v and k in carrier_fields and k in field_mapping
                },
            }

            if existing:
                update_vals = {
                    k: v
                    for k, v in account_vals.items()
                    if k not in ["company_id", "carrier_id"]
                }
                if update_vals:
                    existing.write(update_vals)
                    success += 1
            else:
                env["carrier.account"].create(account_vals)
                success += 1

        except Exception as e:
            failed += 1
            _logger.error(
                f"Error processing company {data.get('company_id', 'unknown')}: {e}"
            )

    _logger.info(f"Migration completed: {success} successful, {failed} failed")

    # Archive temp table
    cr.execute(
        "ALTER TABLE IF EXISTS temp_dhl_company_data "
        "RENAME TO temp_dhl_company_data_archived"
    )
