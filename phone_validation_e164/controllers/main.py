from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale

from ..models.phone_validation_mixin import phone_format


class WebsiteSaleExt(WebsiteSale):
    @http.route(
        ["/shop/address"],
        type="http",
        methods=["GET", "POST"],
        auth="public",
        website=True,
        sitemap=False,
    )
    def address(self, **kw):
        if "submitted" in kw and kw.get("phone") and kw.get("country_id"):
            country_id = request.env["res.country"].browse(int(kw["country_id"]))
            formated_vals = phone_format(
                kw.get("phone"),
                country_id.code if country_id else None,
                country_id.phone_code if country_id else None,
                force_format="E164",
                raise_exception=False,
            )
            kw.update({"phone": formated_vals})

        return super().address(**kw)
