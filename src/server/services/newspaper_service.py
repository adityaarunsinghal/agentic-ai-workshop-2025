"""
Newspaper Creation and Management Service

Handles all CRUD operations for newspaper drafts including:
- Structure management (sections, layouts)
- Article management (adding, formatting, highlighting)
- Editorial elements (notes, themes, stats)
- Metadata management
- Preview and validation

Works with JSON newspaper data structures stored in files.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastmcp.utilities.logging import get_logger


class NewspaperService:
    """
    Service for managing newspaper drafts and their components.

    Handles the complete lifecycle of newspaper creation from
    initial draft through formatting to final delivery.
    """

    def __init__(self, data_dir: Path):
        """
        Initialize newspaper service.

        Args:
            data_dir: Directory for storing newspaper drafts
        """
        self.logger = get_logger("NewspaperService")
        self.data_dir = Path(data_dir)
        self.newspapers_dir = self.data_dir / "newspapers"
        self.newspapers_dir.mkdir(parents=True, exist_ok=True)

    # ============= STRUCTURE MANAGEMENT =============

    def create_draft(
        self, title: str, subtitle: str = "", edition_type: str = "standard"
    ) -> Dict:
        """
        Create new newspaper draft.

        Args:
            title: Newspaper title
            subtitle: Optional subtitle
            edition_type: Edition type (morning_brief, deep_dive, breaking, weekly, special, standard)

        Returns:
            Dict with newspaper_id and confirmation
        """
        newspaper_id = f"newspaper_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        draft = {
            "id": newspaper_id,
            "title": title,
            "subtitle": subtitle,
            "edition_type": edition_type,
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat(),
                "article_count": 0,
                "total_reading_time": 0,
                "topics": [],
                "tone": "",
                "target_audience": "",
            },
            "editorial_elements": [],
            "sections": [],
            "table_of_contents": {"enabled": False, "style": "compact"},
        }

        # Save draft
        self._save_draft(newspaper_id, draft)

        self.logger.info(f"Created newspaper draft: {newspaper_id}")
        return {
            "success": True,
            "newspaper_id": newspaper_id,
            "title": title,
            "edition_type": edition_type,
        }

    def add_section(
        self,
        newspaper_id: str,
        section_title: str,
        layout: str = "grid",
        position: Optional[int] = None,
    ) -> Dict:
        """
        Add section to newspaper.

        Args:
            newspaper_id: Newspaper ID
            section_title: Section title
            layout: Layout type (grid, single-column, featured, timeline)
            position: Optional position (None = append)

        Returns:
            Dict with success status
        """
        draft = self._load_draft(newspaper_id)
        if not draft:
            return {"success": False, "error": f"Newspaper {newspaper_id} not found"}

        # Validate layout
        valid_layouts = ["grid", "single-column", "featured", "timeline"]
        if layout not in valid_layouts:
            return {
                "success": False,
                "error": f"Invalid layout. Must be one of: {valid_layouts}",
            }

        section = {
            "title": section_title,
            "layout": layout,
            "articles": [],
            "editorial_elements": [],
        }

        if position is not None and 0 <= position <= len(draft["sections"]):
            draft["sections"].insert(position, section)
        else:
            draft["sections"].append(section)

        draft["metadata"]["last_modified"] = datetime.now().isoformat()
        self._save_draft(newspaper_id, draft)

        self.logger.debug(f"Added section '{section_title}' to {newspaper_id}")
        return {"success": True, "section_title": section_title, "layout": layout}

    def reorder_sections(self, newspaper_id: str, section_order: List[str]) -> Dict:
        """
        Reorder sections in newspaper.

        Args:
            newspaper_id: Newspaper ID
            section_order: List of section titles in desired order

        Returns:
            Dict with success status
        """
        draft = self._load_draft(newspaper_id)
        if not draft:
            return {"success": False, "error": f"Newspaper {newspaper_id} not found"}

        # Create mapping of title to section
        section_map = {s["title"]: s for s in draft["sections"]}

        # Reorder
        reordered = []
        for title in section_order:
            if title in section_map:
                reordered.append(section_map[title])
            else:
                return {"success": False, "error": f"Section '{title}' not found"}

        draft["sections"] = reordered
        draft["metadata"]["last_modified"] = datetime.now().isoformat()
        self._save_draft(newspaper_id, draft)

        self.logger.debug(f"Reordered sections in {newspaper_id}")
        return {"success": True, "section_order": section_order}

    def set_section_layout(
        self, newspaper_id: str, section_title: str, layout: str
    ) -> Dict:
        """
        Change section layout.

        Args:
            newspaper_id: Newspaper ID
            section_title: Section title
            layout: New layout type

        Returns:
            Dict with success status
        """
        draft = self._load_draft(newspaper_id)
        if not draft:
            return {"success": False, "error": f"Newspaper {newspaper_id} not found"}

        section = self._find_section(draft, section_title)
        if not section:
            return {"success": False, "error": f"Section '{section_title}' not found"}

        valid_layouts = ["grid", "single-column", "featured", "timeline"]
        if layout not in valid_layouts:
            return {
                "success": False,
                "error": f"Invalid layout. Must be one of: {valid_layouts}",
            }

        section["layout"] = layout
        draft["metadata"]["last_modified"] = datetime.now().isoformat()
        self._save_draft(newspaper_id, draft)

        return {"success": True, "section_title": section_title, "layout": layout}

    def remove_section(self, newspaper_id: str, section_title: str) -> Dict:
        """
        Remove section from newspaper.

        Args:
            newspaper_id: Newspaper ID
            section_title: Section title

        Returns:
            Dict with success status
        """
        draft = self._load_draft(newspaper_id)
        if not draft:
            return {"success": False, "error": f"Newspaper {newspaper_id} not found"}

        draft["sections"] = [
            s for s in draft["sections"] if s["title"] != section_title
        ]
        draft["metadata"]["last_modified"] = datetime.now().isoformat()
        self._save_draft(newspaper_id, draft)

        return {"success": True, "section_title": section_title}

    # ============= ARTICLE MANAGEMENT =============

    def add_article(
        self,
        newspaper_id: str,
        section_title: str,
        article_data: Dict,
        placement: str = "standard",
    ) -> Dict:
        """
        Add article to section.

        Args:
            newspaper_id: Newspaper ID
            section_title: Section title
            article_data: Article dict with title, content, url, author, source
            placement: Placement type (lead, standard, sidebar, quick-read)

        Returns:
            Dict with success status
        """
        draft = self._load_draft(newspaper_id)
        if not draft:
            return {"success": False, "error": f"Newspaper {newspaper_id} not found"}

        section = self._find_section(draft, section_title)
        if not section:
            return {"success": False, "error": f"Section '{section_title}' not found"}

        # Validate placement
        valid_placements = ["lead", "standard", "sidebar", "quick-read"]
        if placement not in valid_placements:
            return {
                "success": False,
                "error": f"Invalid placement. Must be one of: {valid_placements}",
            }

        # Create article with defaults
        article = {
            "title": article_data.get("title", "Untitled")[:100],  # Limit title length
            "content": article_data.get("content", ""),
            "url": article_data.get("url", ""),
            "author": article_data.get("author", ""),
            "source": article_data.get("source", ""),
            "placement": placement,
            "format": {
                "show_image": False,
                "image_url": "",
                "image_caption": "",
                "pull_quote": "",
                "key_points": [],
                "callout_box": "",
                "code_snippet": "",
                "reading_time": 0,
                "highlight_type": "",
            },
            "metadata": {
                "added_at": datetime.now().isoformat(),
                "tags": article_data.get("tags", []),
                "word_count": len(article_data.get("content", "").split()),
            },
            "related_articles": [],
        }

        # Calculate reading time (200 words per minute)
        article["format"]["reading_time"] = max(
            1, article["metadata"]["word_count"] // 200
        )

        section["articles"].append(article)

        # Update newspaper metadata
        draft["metadata"]["article_count"] = sum(
            len(s["articles"]) for s in draft["sections"]
        )
        draft["metadata"]["total_reading_time"] = sum(
            sum(a["format"]["reading_time"] for a in s["articles"])
            for s in draft["sections"]
        )
        draft["metadata"]["last_modified"] = datetime.now().isoformat()

        try:
            self._save_draft(newspaper_id, draft)
        except Exception as e:
            self.logger.error(f"Failed to save draft after adding article: {e}")
            raise

        self.logger.debug(
            f"Added article '{article['title']}' to {newspaper_id}/{section_title}"
        )
        return {
            "success": True,
            "article_title": article["title"],
            "section": section_title,
            "reading_time": article["format"]["reading_time"],
        }

    def set_article_format(
        self,
        newspaper_id: str,
        section_title: str,
        article_title: str,
        format_options: Dict,
    ) -> Dict:
        """
        Apply formatting to an article.

        Args:
            newspaper_id: Newspaper ID
            section_title: Section title
            article_title: Article title
            format_options: Dict with formatting options

        Returns:
            Dict with success status
        """
        draft = self._load_draft(newspaper_id)
        if not draft:
            return {"success": False, "error": f"Newspaper {newspaper_id} not found"}

        section = self._find_section(draft, section_title)
        if not section:
            return {"success": False, "error": f"Section '{section_title}' not found"}

        article = self._find_article(section, article_title)
        if not article:
            return {"success": False, "error": f"Article '{article_title}' not found"}

        # Update format options
        article["format"].update(format_options)
        draft["metadata"]["last_modified"] = datetime.now().isoformat()
        self._save_draft(newspaper_id, draft)

        return {"success": True, "article_title": article_title, "format_applied": True}

    def highlight_article(
        self,
        newspaper_id: str,
        section_title: str,
        article_title: str,
        highlight_type: str,
    ) -> Dict:
        """
        Add highlight badge to article.

        Args:
            newspaper_id: Newspaper ID
            section_title: Section title
            article_title: Article title
            highlight_type: Type (breaking, trending, exclusive, deep-dive)

        Returns:
            Dict with success status
        """
        valid_types = ["breaking", "trending", "exclusive", "deep-dive"]
        if highlight_type not in valid_types:
            return {
                "success": False,
                "error": f"Invalid highlight type. Must be one of: {valid_types}",
            }

        return self.set_article_format(
            newspaper_id,
            section_title,
            article_title,
            {"highlight_type": highlight_type},
        )

    def link_related_articles(
        self, newspaper_id: str, article_title: str, related_titles: List[str]
    ) -> Dict:
        """
        Link related articles within newspaper.

        Args:
            newspaper_id: Newspaper ID
            article_title: Main article title
            related_titles: List of related article titles

        Returns:
            Dict with success status
        """
        draft = self._load_draft(newspaper_id)
        if not draft:
            return {"success": False, "error": f"Newspaper {newspaper_id} not found"}

        # Find the main article
        main_article = None
        for section in draft["sections"]:
            article = self._find_article(section, article_title)
            if article:
                main_article = article
                break

        if not main_article:
            return {"success": False, "error": f"Article '{article_title}' not found"}

        main_article["related_articles"] = related_titles
        draft["metadata"]["last_modified"] = datetime.now().isoformat()
        self._save_draft(newspaper_id, draft)

        return {
            "success": True,
            "article_title": article_title,
            "related_count": len(related_titles),
        }

    # ============= EDITORIAL ELEMENTS =============

    def add_editors_note(
        self,
        newspaper_id: str,
        content: str,
        placement: str = "top",
        style: str = "standard",
    ) -> Dict:
        """
        Add editor's note to newspaper.

        Args:
            newspaper_id: Newspaper ID
            content: Note content
            placement: Placement (top, bottom, section:<name>)
            style: Style (standard, highlighted, sidebar)

        Returns:
            Dict with success status
        """
        draft = self._load_draft(newspaper_id)
        if not draft:
            return {"success": False, "error": f"Newspaper {newspaper_id} not found"}

        note = {
            "type": "editors_note",
            "content": content,
            "placement": placement,
            "style": style,
        }

        draft["editorial_elements"].append(note)
        draft["metadata"]["last_modified"] = datetime.now().isoformat()
        self._save_draft(newspaper_id, draft)

        return {"success": True, "element_type": "editors_note"}

    def add_theme_highlight(
        self,
        newspaper_id: str,
        theme: str,
        description: str,
        related_articles: List[str],
    ) -> Dict:
        """
        Add theme/trend highlight connecting multiple articles.

        Args:
            newspaper_id: Newspaper ID
            theme: Theme name
            description: Theme description
            related_articles: List of related article titles

        Returns:
            Dict with success status
        """
        draft = self._load_draft(newspaper_id)
        if not draft:
            return {"success": False, "error": f"Newspaper {newspaper_id} not found"}

        highlight = {
            "type": "theme_highlight",
            "theme": theme,
            "description": description,
            "related_articles": related_articles,
        }

        draft["editorial_elements"].append(highlight)
        draft["metadata"]["last_modified"] = datetime.now().isoformat()
        self._save_draft(newspaper_id, draft)

        return {"success": True, "element_type": "theme_highlight", "theme": theme}

    def add_stats_callout(
        self,
        newspaper_id: str,
        section_title: str,
        stats: List[Dict],
        position: str = "top",
    ) -> Dict:
        """
        Add statistics callout to section.

        Args:
            newspaper_id: Newspaper ID
            section_title: Section title
            stats: List of {label, value, context} dicts
            position: Position (top, bottom, sidebar)

        Returns:
            Dict with success status
        """
        draft = self._load_draft(newspaper_id)
        if not draft:
            return {"success": False, "error": f"Newspaper {newspaper_id} not found"}

        section = self._find_section(draft, section_title)
        if not section:
            return {"success": False, "error": f"Section '{section_title}' not found"}

        if "editorial_elements" not in section:
            section["editorial_elements"] = []

        callout = {"type": "stats_callout", "stats": stats, "position": position}

        section["editorial_elements"].append(callout)
        draft["metadata"]["last_modified"] = datetime.now().isoformat()
        self._save_draft(newspaper_id, draft)

        return {
            "success": True,
            "element_type": "stats_callout",
            "section": section_title,
        }

    def add_resource_box(
        self, newspaper_id: str, section_title: str, title: str, resources: List[Dict]
    ) -> Dict:
        """
        Add resource/further reading box to section.

        Args:
            newspaper_id: Newspaper ID
            section_title: Section title
            title: Box title
            resources: List of {title, url, description} dicts

        Returns:
            Dict with success status
        """
        draft = self._load_draft(newspaper_id)
        if not draft:
            return {"success": False, "error": f"Newspaper {newspaper_id} not found"}

        section = self._find_section(draft, section_title)
        if not section:
            return {"success": False, "error": f"Section '{section_title}' not found"}

        if "editorial_elements" not in section:
            section["editorial_elements"] = []

        resource_box = {"type": "resource_box", "title": title, "resources": resources}

        section["editorial_elements"].append(resource_box)
        draft["metadata"]["last_modified"] = datetime.now().isoformat()
        self._save_draft(newspaper_id, draft)

        return {
            "success": True,
            "element_type": "resource_box",
            "section": section_title,
        }

    # ============= METADATA MANAGEMENT =============

    def set_metadata(self, newspaper_id: str, metadata: Dict) -> Dict:
        """
        Set newspaper-level metadata.

        Args:
            newspaper_id: Newspaper ID
            metadata: Metadata dict (tone, target_audience, topics, etc.)

        Returns:
            Dict with success status
        """
        draft = self._load_draft(newspaper_id)
        if not draft:
            return {"success": False, "error": f"Newspaper {newspaper_id} not found"}

        draft["metadata"].update(metadata)
        draft["metadata"]["last_modified"] = datetime.now().isoformat()
        self._save_draft(newspaper_id, draft)

        return {"success": True, "metadata_updated": True}

    def calculate_reading_times(self, newspaper_id: str) -> Dict:
        """
        Recalculate all reading times in newspaper.

        Args:
            newspaper_id: Newspaper ID

        Returns:
            Dict with total reading time
        """
        draft = self._load_draft(newspaper_id)
        if not draft:
            return {"success": False, "error": f"Newspaper {newspaper_id} not found"}

        total_time = 0
        for section in draft["sections"]:
            for article in section["articles"]:
                word_count = article["metadata"]["word_count"]
                reading_time = max(1, word_count // 200)
                article["format"]["reading_time"] = reading_time
                total_time += reading_time

        draft["metadata"]["total_reading_time"] = total_time
        draft["metadata"]["last_modified"] = datetime.now().isoformat()
        self._save_draft(newspaper_id, draft)

        return {"success": True, "total_reading_time": total_time}

    def add_table_of_contents(self, newspaper_id: str, style: str = "compact") -> Dict:
        """
        Enable table of contents.

        Args:
            newspaper_id: Newspaper ID
            style: TOC style (compact, detailed, visual)

        Returns:
            Dict with success status
        """
        draft = self._load_draft(newspaper_id)
        if not draft:
            return {"success": False, "error": f"Newspaper {newspaper_id} not found"}

        valid_styles = ["compact", "detailed", "visual"]
        if style not in valid_styles:
            return {
                "success": False,
                "error": f"Invalid style. Must be one of: {valid_styles}",
            }

        draft["table_of_contents"] = {"enabled": True, "style": style}
        draft["metadata"]["last_modified"] = datetime.now().isoformat()
        self._save_draft(newspaper_id, draft)

        return {"success": True, "toc_style": style}

    # ============= PREVIEW & VALIDATION =============

    def preview_markdown(self, newspaper_id: str) -> Dict:
        """
        Generate markdown preview of newspaper.

        Args:
            newspaper_id: Newspaper ID

        Returns:
            Dict with preview text
        """
        draft = self._load_draft(newspaper_id)
        if not draft:
            return {"success": False, "error": f"Newspaper {newspaper_id} not found"}

        preview = f"# {draft['title']}\n"
        if draft.get("subtitle"):
            preview += f"*{draft['subtitle']}*\n"
        preview += f"\n**Edition:** {draft['edition_type']}\n"
        preview += f"**Created:** {draft['metadata']['created_at'][:10]}\n"
        preview += f"**Articles:** {draft['metadata']['article_count']}\n"
        preview += (
            f"**Reading Time:** {draft['metadata']['total_reading_time']} minutes\n\n"
        )

        # Editorial elements
        for elem in draft.get("editorial_elements", []):
            if elem["type"] == "editors_note":
                preview += f"**📝 Editor's Note:** {elem['content'][:100]}...\n\n"
            elif elem["type"] == "theme_highlight":
                preview += f"**🎯 Theme:** {elem['theme']} - {elem['description'][:100]}...\n\n"

        # Sections
        for section in draft["sections"]:
            preview += f"## {section['title']} ({section['layout']} layout)\n"
            preview += f"**Articles:** {len(section['articles'])}\n\n"

            for article in section["articles"]:
                preview += f"### {article['title']}\n"
                preview += f"*{article['placement']} | {article['format']['reading_time']} min*\n"
                if article["format"]["highlight_type"]:
                    preview += f"**[{article['format']['highlight_type'].upper()}]**\n"
                preview += f"{article['content'][:150]}...\n\n"

        return {"success": True, "preview": preview}

    def get_stats(self, newspaper_id: str) -> Dict:
        """
        Get newspaper statistics.

        Args:
            newspaper_id: Newspaper ID

        Returns:
            Dict with statistics
        """
        draft = self._load_draft(newspaper_id)
        if not draft:
            return {"success": False, "error": f"Newspaper {newspaper_id} not found"}

        stats = {
            "newspaper_id": newspaper_id,
            "title": draft["title"],
            "edition_type": draft["edition_type"],
            "total_articles": draft["metadata"]["article_count"],
            "total_reading_time": draft["metadata"]["total_reading_time"],
            "section_count": len(draft["sections"]),
            "sections": [],
        }

        for section in draft["sections"]:
            stats["sections"].append(
                {
                    "title": section["title"],
                    "layout": section["layout"],
                    "article_count": len(section["articles"]),
                }
            )

        return {"success": True, "stats": stats}

    def validate(self, newspaper_id: str) -> Dict:
        """
        Validate newspaper for issues.

        Args:
            newspaper_id: Newspaper ID

        Returns:
            Dict with validation results
        """
        draft = self._load_draft(newspaper_id)
        if not draft:
            return {"success": False, "error": f"Newspaper {newspaper_id} not found"}

        issues = []
        warnings = []

        # Check for empty sections
        for section in draft["sections"]:
            if not section["articles"]:
                warnings.append(f"Section '{section['title']}' is empty")

        # Check article count
        if draft["metadata"]["article_count"] == 0:
            issues.append("Newspaper has no articles")

        # Check for missing content
        for section in draft["sections"]:
            for article in section["articles"]:
                if not article["content"]:
                    issues.append(f"Article '{article['title']}' has no content")

        # Check reading time
        if draft["metadata"]["total_reading_time"] == 0:
            warnings.append("Reading time not calculated")

        return {
            "success": True,
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
        }

    # ============= HELPER METHODS =============

    def _save_draft(self, newspaper_id: str, draft: Dict) -> None:
        """Save newspaper draft to JSON file."""
        draft_file = self.newspapers_dir / f"{newspaper_id}.json"
        with open(draft_file, "w") as f:
            json.dump(draft, f, indent=2, default=str)

    def _load_draft(self, newspaper_id: str) -> Optional[Dict]:
        """Load newspaper draft from JSON file."""
        draft_file = self.newspapers_dir / f"{newspaper_id}.json"
        if not draft_file.exists():
            return None

        with open(draft_file, "r") as f:
            return json.load(f)

    def _find_section(self, draft: Dict, section_title: str) -> Optional[Dict]:
        """Find section by title."""
        for section in draft["sections"]:
            if section["title"] == section_title:
                return section
        return None

    def _find_article(self, section: Dict, article_title: str) -> Optional[Dict]:
        """Find article by title in section."""
        for article in section["articles"]:
            if article["title"] == article_title:
                return article
        return None

    def get_newspaper_data(self, newspaper_id: str) -> Optional[Dict]:
        """Get complete newspaper data structure."""
        return self._load_draft(newspaper_id)
