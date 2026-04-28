UPDATE carrier_account
   SET account = '3333333333',
       dhl_userid = NULL,
       password = 'SandboxPasswort2023!',
       dhl_api_key = NULL,
       dhl_api_secret = NULL,
       dhl_access_token = NULL,
       dhl_parcel_de_api_url = 'https://api-sandbox.dhl.com'
   WHERE delivery_type = 'dhl_parcel_de_provider';
UPDATE delivery_carrier
    SET prod_environment = false
    WHERE delivery_type = 'dhl_parcel_de_provider';
