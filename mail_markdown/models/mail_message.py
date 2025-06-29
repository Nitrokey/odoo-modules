import re
from odoo import models, api


class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model_create_multi
    def create(self, vals_list):
        """Process markdown content when creating messages."""
        for vals in vals_list:
            if vals.get('body'):
                vals['body'] = self._process_markdown_in_body(vals['body'])
        return super().create(vals_list)

    def write(self, vals):
        """Process markdown content when updating messages."""
        if vals.get('body'):
            vals['body'] = self._process_markdown_in_body(vals['body'])
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
        
        # Check for common markdown patterns
        markdown_patterns = [
            r'\*\*.*?\*\*',  # Bold **text**
            r'__.*?__',      # Underline __text__
            r'\*.*?\*',      # Italic *text*
            r'_.*?_',        # Italic _text_
            r'~~.*?~~',      # Strikethrough ~~text~~
            r'`.*?`',        # Inline code `code`
            r'```.*?```',    # Code blocks ```code```
            r'\[.*?\]\(.*?\)',  # Links [text](url)
            r'^#{1,6}\s',    # Headers # ## ###
            r'^\s*[\*\-\+]\s',  # Unordered lists
            r'^\s*\d+\.\s',  # Ordered lists
            r'^>\s',         # Blockquotes
        ]
        
        for pattern in markdown_patterns:
            if re.search(pattern, text, re.MULTILINE):
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

        html = markdown_text

        # Convert bold text (**text**)
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)

        # Convert italic text (*text* or _text_)
        html = re.sub(r'(?<!\*)\*(?!\*)([^*]+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', html)
        html = re.sub(r'(?<!_)_(?!_)([^_]+?)(?<!_)_(?!_)', r'<em>\1</em>', html)

        # Convert underline text (__text__)
        html = re.sub(r'__(.*?)__', r'<u>\1</u>', html)

        # Convert strikethrough text (~~text~~)
        html = re.sub(r'~~(.*?)~~', r'<del>\1</del>', html)

        # Convert inline code (`code`)
        html = re.sub(r'`([^`]+?)`', r'<code>\1</code>', html)

        # Convert code blocks (```code```)
        html = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', html, flags=re.DOTALL)

        # Convert links [text](url)
        html = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<a href="\2" target="_blank">\1</a>', html)

        # Convert headers
        html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

        # Convert unordered lists
        html = re.sub(r'^[\*\-\+] (.*)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)
        html = re.sub(r'</ul>\s*<ul>', '', html)

        # Convert ordered lists
        html = re.sub(r'^\d+\. (.*)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        # This is a simplified approach - in reality, you'd want more sophisticated list handling

        # Convert line breaks
        html = html.replace('\n', '<br/>')

        # Convert blockquotes
        html = re.sub(r'^> (.*)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)

        return html

    @api.model
    def _get_markdown_preview(self, markdown_text):
        """
        Get HTML preview of markdown text.
        This method can be called from the frontend to show live preview.
        """
        return self._markdown_to_html(markdown_text)
