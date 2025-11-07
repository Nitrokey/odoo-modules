import re

from odoo import http
from odoo.http import request

from odoo.addons.web.controllers.home import Home as WebHome


class Website(WebHome):
    """Override Odoo's default language switch to support translated URLs."""

    @http.route(
        "/website/lang/<lang>",
        type="http",
        auth="public",
        website=True,
        multilang=False,
    )
    def change_lang(self, lang, r="/", **kwargs):
        """Redirect user to translated URL when changing language."""
        website = request.website
        default_lang = website.default_lang_id.url_code

        # Resolve target language code
        lang_data = request.env["res.lang"]._get_data(url_code=lang)
        lang_code = lang_data.code or lang
        request.update_context(lang=lang_code)

        # Remove any language prefix (e.g. /de/contactus → /contactus)
        clean_url = re.sub(r"^/[a-z]{2}(?:_[A-Z]{2})?/", "/", r or "/")

        # Get translated page URL (if available)
        translated_url = self._get_translated_url(clean_url, lang_code)

        # Build redirect target
        redirect_url = (
            f"/{lang}{translated_url}" if lang != default_lang else translated_url
        )
        redirect = request.redirect(redirect_url)
        redirect.set_cookie("frontend_lang", lang_code)
        return redirect

    def _get_translated_url(self, src_url, lang_code):
        """Return translated page URL for the given language."""
        web_page = request.env["website.page"].sudo()
        clean_url = re.sub(r"^/[a-z]{2}(?:_[A-Z]{2})?/", "/", src_url or "/")

        # Try to find the page in ANY language to get the base source
        page = None
        for lang in web_page.env["res.lang"].search([("active", "=", True)]):
            candidate = web_page.with_context(lang=lang.code).search(
                [("url", "=", clean_url)], limit=1
            )
            if candidate:
                page = candidate
                break

        # Return translated version or fallback to clean URL
        return page.with_context(lang=lang_code).url if page else clean_url
