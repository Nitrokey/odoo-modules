from odoo import http
from odoo.http import request

from odoo.addons.web.controllers.home import Home as WebHome


class Website(WebHome):
    @http.route(
        "/website/lang/<lang>",
        type="http",
        auth="public",
        website=True,
        multilang=False,
    )
    def change_lang(self, lang, r="/", **kwargs):
        """Override website language change to support translated menu URLs.
        Handle language change while keeping translated URLs."""
        TRANSLATE = request.env["ir.translation"].sudo()
        lang_code = request.env["res.lang"]._lang_get_code(lang)
        page_url = r.replace(f"/{lang}", "")
        trans_r = r.replace(f"{lang}/", "")

        # Search translation record matching language and source URL
        trans_rec = TRANSLATE.search(
            [("lang", "=", lang_code), ("src", "=", trans_r)], limit=1
        )

        if trans_rec:
            r = f"/{lang}{(trans_rec.value or trans_rec.src)}"
        else:
            # Try reverse lookup by translated value or src
            trans_val = TRANSLATE.search(
                [("value", "=", page_url)], limit=1
            ) or TRANSLATE.search([("src", "=", page_url)], limit=1)

            if trans_val:
                src = trans_val.src
                trans_lang = TRANSLATE.search(
                    [("src", "=", src), ("lang", "=", lang_code)], limit=1
                )
                trans_text = trans_lang.value or trans_lang.src if trans_lang else src
                r = f"/{lang}{trans_text}"

        # Call parent Home controller’s language switch
        return super().change_lang(lang=lang, r=r, **kwargs)
