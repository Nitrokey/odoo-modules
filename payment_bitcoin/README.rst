=========================
Bitcoin Payment Acquirer
=========================

Payment Acquirer: Bitcoin Transfer Implementation

Testing
-------
1. Sign in as an Administrator.

2. **Accounting→ Configuration→ Payment Providers→ Bitcoin**.

   In the State field, **Enabled** or **Test Mode** should be selected.

3. Below the **State** field, select the tab **Configuration**.
   
   Click on the link **“→ Enable Payment Methods”** it will take you to the **Activation** section, where you will see one line with two columns:
   
   Name: Bitcoin
   
   Active: there is a toggle here, the toggle must be green
   
   **If the toggle is not green, the Bitcoin payment option will not be available as an option to execute the  test payment.**

4. Go back to the **Payment Providers→ Bitcoin** section. In the top middle, you should see a button. If the text on the button shows “Unpublished”, click on it because it should be displaying “Published”.

5. **Configuration→ Bitcoin Addresses→ “+ New”** button. 
   
   In the Address field, paste a Bitcoin address:
   Example: bc1qxy2kgdygjrsqtzq2n0yrf2493p
   
   This is a Bitcoin Address that was found on `Blockchain.com <https://www.blockchain.com/explorer/addresses/btc/bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh>`_. If you scroll down, you will be able to see the transactions in the **Transactions** section. Under the **Transaction ID** you will be able to see the **date** and **time**    at which the transaction was made on.

6. Set the **“Deadline (in minutes)“** field in the Bitcoin Configuration tab to cover the time since the last transaction on the Bitcoin Address was made.

   Example: If the last transaction was one week ago (10,080 minutes), set the value to **at least 11,520 minutes (8 days)**.  

7. Set the **“Orders older than (In hours)“** field in the Bitcoin Configuration tab to cover the time since the last transaction on the Bitcoin Address was made.

   Example: If the last transaction was one week ago (168 hours), set the value to **at least 192 hours (8 days)**.  

8. Open a new private window in your browser (you do not need to log in).

9. Go through the normal payment process:
   
   **Shop→ Select an item→ Checkout→ Address→ Bitcoin→ Pay Now**.
   
   Ensure that the product selected for testing has a price lower than the value of the last Bitcoin transaction.
   
   Example: If the last transaction was 50 €, select a product priced below this amount (for example 1 €) when performing the test payment.
   
   **If you receive a message saying that the Bitcoin payment method is not available, check if you executed the above steps correctly.**
   
10. To confirm the order and register the payment: 

    **Administrator window→ Settings→ Technical→ Scheduled Actions→ Select your order→ Run Manually**.

11. **Sales→ Orders→** Sale order number row (for example SO10134)
    
    Check if the sale order status automatically changes from "Quotation Sent" to “Sales Order" (confirmed state).
    
    Check if the payment is registered to the corresponding invoice.
    
    To go to the invoice, click on the “Invoices” button located in the upper middle of the corresponding Sales order page
    
12. To make a second order using the same Bitcoin Address payment:
    
    **Administrator Window→ Bitcoin Address→ Order Assigned field→**  Remove the order number from the previous order.
    
