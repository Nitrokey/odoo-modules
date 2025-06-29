import logging
import re

from odoo import api, models

_logger = logging.getLogger(__name__)


class MailMessage(models.Model):
    _inherit = "mail.message"

    @api.model_create_multi
    def create(self, vals_list):
        """Process markdown content when creating messages."""
        for vals in vals_list:
            if vals.get("body"):
                vals["body"] = self._process_markdown_in_body(vals["body"])
        return super().create(vals_list)

    def write(self, vals):
        """Process markdown content when updating messages."""
        if vals.get("body"):
            vals["body"] = self._process_markdown_in_body(vals["body"])
        return super().write(vals)

    def _process_markdown_in_body(self, body):
        """
        Process markdown syntax in message body if it contains markdown.
        Only processes if the body appears to contain markdown syntax.
        """
        if not body or not self._contains_markdown(body):
            return body
        return self._markdown_to_html(body)

    def _contains_markdown(self, text):
        """
        Check if text contains common markdown patterns.
        """
        if not text:
            return False

        # Handle both \n and <br> as line separators for detection
        # Also handle HTML entities that Odoo may have escaped
        text_normalized = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
        text_normalized = text_normalized.replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&")
        
        # Check for common markdown patterns
        markdown_patterns = [
            r"\*\*.*?\*\*",  # Bold **text**
            r"__.*?__",  # Underline __text__
            r"\*.*?\*",  # Italic *text*
            r"_.*?_",  # Italic _text_
            r"~~.*?~~",  # Strikethrough ~~text~~
            r"`.*?`",  # Inline code `code`
            r"```.*?```",  # Code blocks ```code```
            r"\[.*?\]\(.*?\)",  # Links [text](url)
            r"(^|\n)#{1,6}\s",  # Headers # ## ###
            r"(^|\n)\s*[\*\-\+]\s",  # Unordered lists
            r"(^|\n)\s*\d+\.\s",  # Ordered lists
            r"(^|\n)>\s",  # Blockquotes
        ]

        for pattern in markdown_patterns:
            if re.search(pattern, text_normalized, re.MULTILINE):
                return True
        return False

    def _markdown_to_html(self, markdown_text):
        """
        Convert markdown text to HTML.
        This is a simple implementation for basic markdown features.
        For more advanced features, consider using a proper markdown library.
        """
        if not markdown_text:
            return markdown_text

        # First handle HTML entities and line breaks
        html = markdown_text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
        html = html.replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&")

        # Process code blocks first (they span multiple lines)
        html = re.sub(
            r"```(.*?)```", r"<pre><code>\1</code></pre>", html, flags=re.DOTALL
        )

        # Now process line-by-line for line-dependent formatting
        lines = html.split("\n")
        processed_lines = []
        in_ul = False
        in_ol = False

        for line in lines:
            _logger.info(f"Processing line: '{line}'")
            
            # Convert headers (must be at start of line)
            if re.match(r"^### (.*)$", line):
                _logger.info("Matched header 3")
                line = re.sub(r"^### (.*)$", r"<h3>\1</h3>", line)
            elif re.match(r"^## (.*)$", line):
                _logger.info("Matched header 2")
                line = re.sub(r"^## (.*)$", r"<h2>\1</h2>", line)
            elif re.match(r"^# (.*)$", line):
                _logger.info("Matched header 1")
                line = re.sub(r"^# (.*)$", r"<h1>\1</h1>", line)

            # Convert unordered lists
            elif re.match(r"^\s*[\*\-\+] (.*)$", line):
                _logger.info("Matched unordered list")
                if not in_ul:
                    processed_lines.append("<ul>")
                    in_ul = True
                line = re.sub(r"^\s*[\*\-\+] (.*)$", r"<li>\1</li>", line)

            # Convert ordered lists
            elif re.match(r"^\s*\d+\. (.*)$", line):
                _logger.info("Matched ordered list")
                if not in_ol:
                    processed_lines.append("<ol>")
                    in_ol = True
                line = re.sub(r"^\s*\d+\. (.*)$", r"<li>\1</li>", line)

            # Convert blockquotes
            elif re.match(r"^>\s*(.*)$", line):
                _logger.info("Matched blockquote with space")
                line = re.sub(r"^>\s*(.*)$", r"<blockquote>\1</blockquote>", line)
            elif re.match(r"^>(.*)$", line):
                _logger.info("Matched blockquote without space")
                line = re.sub(r"^>(.*)$", r"<blockquote>\1</blockquote>", line)

            # Handle end of lists
            else:
                _logger.info("No match - handling list endings")
                if in_ul:
                    processed_lines.append("</ul>")
                    in_ul = False
                if in_ol:
                    processed_lines.append("</ol>")
                    in_ol = False

            _logger.info(f"Processed line result: '{line}'")
            processed_lines.append(line)

        # Close any open lists at the end
        if in_ul:
            processed_lines.append("</ul>")
        if in_ol:
            processed_lines.append("</ol>")

        # Now handle inline formatting on the processed text
        html = "\n".join(processed_lines)

        # Convert bold text (**text**)
        html = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", html)

        # Convert italic text (*text* or _text_)
        html = re.sub(r"(?<!\*)\*(?!\*)([^*]+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", html)
        html = re.sub(r"(?<!_)_(?!_)([^_]+?)(?<!_)_(?!_)", r"<em>\1</em>", html)

        # Convert underline text (__text__)
        html = re.sub(r"__(.*?)__", r"<u>\1</u>", html)

        # Convert strikethrough text (~~text~~)
        html = re.sub(r"~~(.*?)~~", r"<del>\1</del>", html)

        # Convert inline code (`code`)
        html = re.sub(r"`([^`]+?)`", r"<code>\1</code>", html)

        # Convert links [text](url)
        html = re.sub(
            r"\[([^\]]+?)\]\(([^)]+?)\)", r'<a href="\2" target="_blank">\1</a>', html
        )

        return html

    @api.model
    def _get_markdown_preview(self, markdown_text):
        """
        Get HTML preview of markdown text.
        This method can be called from the frontend to show live preview.
        """
        return self._markdown_to_html(markdown_text)
