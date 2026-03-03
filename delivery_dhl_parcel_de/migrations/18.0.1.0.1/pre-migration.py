import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Store res.company DHL data before carrier.account exists"""
    _logger.info("Starting pre-migration: Storing DHL data from res.company")

    # First, check if the fields exist in res.company
    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'res_company'
        AND column_name IN (
            'use_dhl_parcel_de_shipping_provider',
            'dhl_parcel_de_api_url',
            'dhl_userid',
            'dhl_password',
            'dhl_api_key',
            'dhl_api_secret',
            'dhl_tracking_url',
            'dhl_access_token'
        )
    """)

    existing_columns = [row[0] for row in cr.fetchall()]
    _logger.info(f"Found columns in res.company: {existing_columns}")

    # Create a temporary table to store the data
    # Using IF NOT EXISTS to avoid errors if script runs multiple times
    cr.execute("""
        CREATE TEMP TABLE IF NOT EXISTS temp_dhl_company_data (
            company_id INTEGER,
            use_dhl_parcel_de_shipping_provider BOOLEAN,
            dhl_parcel_de_api_url VARCHAR,
            dhl_userid VARCHAR,
            dhl_password VARCHAR,
            dhl_api_key VARCHAR,
            dhl_api_secret VARCHAR,
            dhl_tracking_url VARCHAR,
            dhl_access_token VARCHAR
        )
    """)

    # Clear existing data in temp table (in case of re-run)
    cr.execute("DELETE FROM temp_dhl_company_data")

    # Insert data from res.company
    cr.execute("""
        INSERT INTO temp_dhl_company_data (
            company_id,
            use_dhl_parcel_de_shipping_provider,
            dhl_parcel_de_api_url,
            dhl_userid,
            dhl_password,
            dhl_api_key,
            dhl_api_secret,
            dhl_tracking_url,
            dhl_access_token
        )
        SELECT
            id as company_id,
            use_dhl_parcel_de_shipping_provider,
            dhl_parcel_de_api_url,
            dhl_userid,
            dhl_password,
            dhl_api_key,
            dhl_api_secret,
            dhl_tracking_url,
            dhl_access_token
        FROM res_company
        WHERE use_dhl_parcel_de_shipping_provider = true
    """)

    # Get count of records migrated
    cr.execute("SELECT COUNT(*) FROM temp_dhl_company_data")
    count = cr.fetchone()[0]

    _logger.info(
        f"Successfully stored {count} companies with DHL enabled in temporary table"
    )

    # Optional: Verify the data was stored correctly
    if count > 0:
        cr.execute("SELECT company_id, dhl_userid FROM temp_dhl_company_data LIMIT 5")
        sample_data = cr.fetchall()
        _logger.info(f"Sample data from temp table: {sample_data}")
