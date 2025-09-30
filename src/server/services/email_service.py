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
            self.username = email_settings.get("username", "")
            self.password = email_settings.get("password", "")
            self.from_email = email_settings.get("from_email", "newspaper@localhost")
            self.from_name = email_settings.get("from_name", "Newspaper Creation Agent")
        else:
            # EmailSettings object
            self.server = email_settings.server
            self.port = email_settings.port
            self.use_tls = email_settings.use_tls
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

    def send_newspaper(self, newspaper_data: Dict, subject: str = None) -> Dict:
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
            html_content = self._create_html_version(newspaper_data)

            # Attach both versions
            text_part = MIMEText(text_content, "plain", "utf-8")
            html_part = MIMEText(html_content, "html", "utf-8")

            msg.attach(text_part)
            msg.attach(html_part)

            # Send email
            if self.use_tls:
                server = smtplib.SMTP(self.server, self.port)
                server.starttls()
            else:
                server = smtplib.SMTP(self.server, self.port)

            if self.username and self.password:
                server.login(self.username, self.password)

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

    def _create_html_version(self, newspaper_data: Dict) -> str:
        """Create HTML version using authentic newspaper template."""
        template = self.jinja_env.get_template("newspaper_email.html")

        # Transform data for template
        organized_articles = self._organize_articles(newspaper_data)

        return template.render(
            newspaper_title=newspaper_data.get("title", "The Tech Tribune"),
            current_date=datetime.now().strftime("%A, %B %d, %Y"),
            edition=newspaper_data.get("edition", "Daily Edition"),
            articles=organized_articles,
        )

    def _organize_articles(self, newspaper_data: Dict) -> Dict:
        """Organize articles into front page and columns."""
        sections = newspaper_data.get("sections", [])
        all_articles = []

        # Flatten all articles
        for section in sections:
            all_articles.extend(section.get("articles", []))

        if not all_articles:
            return {"front_page": None, "column_1": [], "column_2": [], "column_3": []}

        # Sort by score if available (use 0 as default)
        all_articles.sort(
            key=lambda x: x.get("score", 0) if isinstance(x, dict) else 0, reverse=True
        )

        # Front page gets top article
        front_page = all_articles[0] if all_articles else None

        # Distribute rest across columns
        remaining = all_articles[1:]
        columns = {"column_1": [], "column_2": [], "column_3": []}

        for i, article in enumerate(remaining):
            column = f"column_{(i % 3) + 1}"
            columns[column].append(article)

        return {"front_page": front_page, **columns}
