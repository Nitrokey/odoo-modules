-- remove DHL credentials and DHL account number on delivery carriers
UPDATE res_company
   SET dhl_userid = NULL,
       dhl_password = NULL,
       dhl_api_key = NULL,
       dhl_api_secret = NULL,
       dhl_access_token = NULL,
       dhl_parcel_de_api_url = 'https://api-sandbox.dhl.com';
UPDATE delivery_carrier
    SET dhl_account_no = NULL,
        prod_environment = false
    WHERE delivery_type = 'dhl_parcel_de_provider';
