# Carrier Deutsche Post

## Operations

The API of Deutsche Post requires to provide prices within requests. Deutsche Post changes their prices every few months. Prices are not gathered dynamically but are hard coded in [inema library](https://pypi.org/project/inema/). Inema supports multiple price lists in parallel but (Python) requires a restart to take those new price lists into account. In consequence, this means for operation:

1. Monitor price changes of Deutsche Post. Usually when being a Portokasse customer, you should receive an email a few weeks in advance with a new price list (CSV) attached.
2. Make sure the new prices are added to inema and that inema version is ideally released. Usually inema's maintainers are helpful in updating those promptly.
3. Update your Odoo system with the required inema version.
4. At the day when new prices come into affect, restart your Odoo system.