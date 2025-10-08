"""
Simple Email Service for Personal Newspaper Delivery

A lightweight SMTP service for sending newspapers to yourself.
Just the essentials - no complex templating or multi-user features.
"""

import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict

import markdown
from fastmcp.utilities.logging import get_logger
from jinja2 import Environment, FileSystemLoader, select_autoescape


class EmailService:
    """Simple email service for personal newspaper delivery."""

    def __init__(self, email_settings):
        """Initialize with email settings."""
        self.logger = get_logger("EmailService")

        # Handle both dict and EmailSettings object
        if isinstance(email_settings, dict):
            # Dictionary input
            self.server = email_settings.get("server", "localhost")
            self.port = email_settings.get("port", 587)
            self.use_tls = email_settings.get("use_tls", True)
            self.use_ssl = email_settings.get("use_ssl", False)
            self.username = email_settings.get("username", "")
            self.password = email_settings.get("password", "")
            self.from_email = email_settings.get("from_email", "newspaper@localhost")
            self.from_name = email_settings.get("from_name", "Newspaper Creation Agent")
        else:
            # EmailSettings object
            self.server = email_settings.server
            self.port = email_settings.port
            self.use_tls = email_settings.use_tls
            self.use_ssl = getattr(email_settings, "use_ssl", False)
            self.username = email_settings.username
            self.password = email_settings.password
            self.from_email = email_settings.from_email
            self.from_name = email_settings.from_name

        # Setup Jinja2 for templates
        template_dir = Path(__file__).parent.parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

        # Add markdown filter
        self.jinja_env.filters["markdown"] = lambda text: (
            markdown.markdown(text) if text else ""
        )

    def send_newspaper(
        self, newspaper_data: Dict, subject: str = None, version: int = 1
    ) -> Dict:
        """
        Send newspaper to your personal email.

        Args:
            newspaper_data: Dict with newspaper content
            subject: Email subject (optional)

        Returns:
            Dict: Success status and details
        """
        try:
            # Create email
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = self.from_email  # Always send to yourself
            msg["Subject"] = (
                subject
                or f"📰 {newspaper_data.get('title', 'Your Newspaper')} - {datetime.now().strftime('%B %d, %Y')}"
            )

            # Create simple text and HTML versions
            text_content = self._create_text_version(newspaper_data)
            html_content = self._create_html_version(newspaper_data, version)

            # Attach both versions
            text_part = MIMEText(text_content, "plain", "utf-8")
            html_part = MIMEText(html_content, "html", "utf-8")

            msg.attach(text_part)
            msg.attach(html_part)

            # Send email - handle both SSL and TLS
            if self.use_ssl:
                # Use SSL (port 465)
                server = smtplib.SMTP_SSL(self.server, self.port, timeout=30)
                self.logger.debug(f"Connected via SSL to {self.server}:{self.port}")
            else:
                # Use TLS (port 587)
                server = smtplib.SMTP(self.server, self.port, timeout=30)
                if self.use_tls:
                    server.starttls()
                    self.logger.debug(f"Started TLS on {self.server}:{self.port}")

            # Login and send
            if self.username and self.password:
                server.login(self.username, self.password)
                self.logger.debug("SMTP login successful")

            server.send_message(msg)
            server.quit()

            self.logger.info("Newspaper sent successfully")
            return {"success": True, "message": "Newspaper delivered to your email"}

        except Exception as e:
            self.logger.error(f"Failed to send newspaper: {e}")
            return {"success": False, "error": str(e)}

    def _create_text_version(self, newspaper_data: Dict) -> str:
        """Create simple text version of newspaper."""
        title = newspaper_data.get("title", "Your Newspaper")
        date = datetime.now().strftime("%B %d, %Y")
        sections = newspaper_data.get("sections", [])

        content = f"{title}\n{date}\n{'=' * len(title)}\n\n"

        for section in sections:
            section_title = section.get("title", "News")
            content += f"{section_title.upper()}\n{'-' * len(section_title)}\n\n"

            for article in section.get("articles", []):
                article_title = article.get("title", "Untitled")
                article_content = article.get("content", article.get("summary", ""))
                source = article.get("source", "")
                url = article.get("url", "")

                content += f"• {article_title}\n"
                if article_content:
                    content += f"  {article_content[:200]}...\n"
                if source:
                    content += f"  Source: {source}\n"
                if url:
                    content += f"  Link: {url}\n"
                content += "\n"

            content += "\n"

        content += f"\n---\nGenerated by Newspaper Creation Agent on {date}"
        return content

    def _create_html_version(self, newspaper_data: Dict, version: int = 1) -> str:
        """Create HTML version using enhanced template."""
        template = self.jinja_env.get_template(f"newspaper_email_v{version}.html")

        return template.render(
            newspaper_title=newspaper_data.get("title", "The Tech Tribune"),
            subtitle=newspaper_data.get("subtitle", ""),
            current_date=datetime.now().strftime("%A, %B %d, %Y"),
            edition=newspaper_data.get("edition_type", "Daily Edition"),
            sections=newspaper_data.get("sections", []),
            editorial_elements=newspaper_data.get("editorial_elements", []),
            table_of_contents=newspaper_data.get(
                "table_of_contents", {"enabled": False}
            ),
            metadata=newspaper_data.get("metadata", {}),
        )
