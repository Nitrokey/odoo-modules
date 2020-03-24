The custom module payment_bitcoin lets customers choose Bitcoin as a payment method. In the backend a bitcoin rate needs to be configured and several Bitcoin addresses. 

Invoicing -> Configuration -> Bitcoin Adresses

These addresses are used only once. When entering Bitcoin addresses there validity is verified by payment_bitcoin. The same Bitcoin address can't be added twice.

Create and Assign an order to its address

Invoicing -> Configuration -> Bitcoin Adresses -> Create

During checkout in ecommerce, customer can choose to pay Bitcoin. If Bitcoin is selected but no Bitcoin address is available, an error is displayed. If a Bitcoin address is available, it will be assigned to the order and the amount in Bitcoin is calculated automatically by fetching the exchange rate online and applying the Bitcoin rate to it (which is kind of additional payment fee). At the checkout confirmation page, the Bitcoin address and the amount to-be-payed is displayed to the user. The amount and Bitcoin address is also send to the customer in the order confirmation email.

Other than fetching the exchange rate, there is no online integration or Blockchain implementation to other services or the Bitcoin network. Bitocin Payments are not known to Odoo. Payments are booked manually and usually "wire transfer" is chosen as a payment method.
