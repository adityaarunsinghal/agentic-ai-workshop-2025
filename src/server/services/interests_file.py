"""
Simple File-Based Interest Management Service

Provides CRUD operations for user interests through a simple interests.md file.
Replaces the complex vector-based interest tracking with a straightforward
file-based approach that's easy to understand and modify.

Features:
- Simple markdown file format for interests
- CRUD operations (Create, Read, Update, Delete)
- Topic and source preference management
- Summary style preferences
- Atomic file operations for consistency
- Comprehensive error handling and logging

The interests.md file serves as the single source of truth for user preferences,
making it easy to inspect, modify, and version control user interests.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from fastmcp.utilities.logging import get_logger


class InterestsFileService:
    """
    File-based service for managing user interests through interests.md.

    Manages user interests, preferred sources, and summary styles through
    a simple markdown file that can be easily edited by users or tools.

    The service handles:
    - Reading and parsing interests.md file
    - Updating interests atomically
    - Managing topics, sources, and preferences
    - Maintaining file format consistency
    """

    def __init__(self, data_dir: Path):
        """
        Initialize interests file service.

        Args:
            data_dir: Directory where interests.md will be stored
        """
        self.logger = get_logger("InterestsFileService")
        self.data_dir = Path(data_dir)
        self.interests_file = self.data_dir / "interests.md"

        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize file if it doesn't exist
        if not self.interests_file.exists():
            self._create_default_file()

    def _create_default_file(self) -> None:
        """Create a default interests.md file with template structure."""
        default_content = """# User Interests
Last Updated: {timestamp}

## Topics
<!-- Add your topics of interest, one per line -->
- Distributed systems
- Python performance
- Database internals

## Preferred Sources
<!-- Your preferred news sources -->
- Hacker News (technical discussions)
- ArXiv (research papers)

## Summary Style
<!-- Your preferred summary style: brief, detailed, technical -->
- Style: detailed
- Include code examples when relevant
- Focus on practical implications

## Notes
<!-- Any additional notes about your interests -->
- Prefer technical depth over surface-level coverage
- Interested in both theory and practical applications
""".format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        try:
            with open(self.interests_file, "w", encoding="utf-8") as f:
                f.write(default_content)
            self.logger.info(f"Created default interests file at {self.interests_file}")
        except Exception as e:
            self.logger.error(f"Failed to create default interests file: {e}")
            raise

    def read_interests(self) -> Dict:
        """
        Read and parse the interests.md file.

        Returns:
            Dict: Parsed interests with topics, sources, style, and notes
        """
        try:
            if not self.interests_file.exists():
                self._create_default_file()

            with open(self.interests_file, "r", encoding="utf-8") as f:
                content = f.read()

            return self._parse_interests_content(content)

        except Exception as e:
            self.logger.error(f"Failed to read interests file: {e}")
            return {
                "topics": [],
                "sources": [],
                "style": "detailed",
                "notes": [],
                "error": str(e),
                "last_updated": "unknown",
            }

    def _parse_interests_content(self, content: str) -> Dict:
        """
        Parse the markdown content into structured data.

        Args:
            content: Raw markdown content from interests.md

        Returns:
            Dict: Structured interests data
        """
        interests = {
            "topics": [],
            "sources": [],
            "style": "detailed",
            "notes": [],
            "last_updated": "unknown",
        }

        # Extract last updated timestamp
        updated_match = re.search(r"Last Updated: (.+)", content)
        if updated_match:
            interests["last_updated"] = updated_match.group(1).strip()

        # Extract topics section
        topics_match = re.search(
            r"## Topics\s*\n(.*?)(?=\n## |\n$)", content, re.DOTALL
        )
        if topics_match:
            topics_section = topics_match.group(1)
            topics = re.findall(r"^- (.+)$", topics_section, re.MULTILINE)
            interests["topics"] = [
                topic.strip() for topic in topics if not topic.startswith("<!--")
            ]

        # Extract sources section
        sources_match = re.search(
            r"## Preferred Sources\s*\n(.*?)(?=\n## |\n$)", content, re.DOTALL
        )
        if sources_match:
            sources_section = sources_match.group(1)
            sources = re.findall(r"^- (.+)$", sources_section, re.MULTILINE)
            interests["sources"] = [
                source.strip() for source in sources if not source.startswith("<!--")
            ]

        # Extract summary style
        style_match = re.search(
            r"## Summary Style\s*\n(.*?)(?=\n## |\n$)", content, re.DOTALL
        )
        if style_match:
            style_section = style_match.group(1)
            style_line_match = re.search(r"- Style: (\w+)", style_section)
            if style_line_match:
                interests["style"] = style_line_match.group(1).strip()

        # Extract notes section
        notes_match = re.search(r"## Notes\s*\n(.*?)$", content, re.DOTALL)
        if notes_match:
            notes_section = notes_match.group(1)
            notes = re.findall(r"^- (.+)$", notes_section, re.MULTILINE)
            interests["notes"] = [
                note.strip() for note in notes if not note.startswith("<!--")
            ]

        return interests

    def add_topics(self, topics: List[str]) -> Dict:
        """
        Add new topics to the interests file.

        Args:
            topics: List of topic strings to add

        Returns:
            Dict: Result with success status and updated topics
        """
        try:
            current_interests = self.read_interests()
            current_topics = set(current_interests.get("topics", []))

            # Add new topics (avoid duplicates)
            new_topics = [topic for topic in topics if topic not in current_topics]
            if not new_topics:
                return {
                    "success": True,
                    "message": "No new topics to add (duplicates filtered)",
                    "added": [],
                    "total_topics": len(current_topics),
                }

            updated_topics = list(current_topics) + new_topics

            # Update the interests file
            self._update_section("topics", updated_topics)

            return {
                "success": True,
                "message": f"Added {len(new_topics)} new topics",
                "added": new_topics,
                "total_topics": len(updated_topics),
            }

        except Exception as e:
            self.logger.error(f"Failed to add topics: {e}")
            return {"success": False, "error": str(e), "added": [], "total_topics": 0}

    def remove_topics(self, topics: List[str]) -> Dict:
        """
        Remove topics from the interests file.

        Args:
            topics: List of topic strings to remove

        Returns:
            Dict: Result with success status and remaining topics
        """
        try:
            current_interests = self.read_interests()
            current_topics = set(current_interests.get("topics", []))

            # Remove specified topics
            topics_to_remove = set(topics)
            remaining_topics = list(current_topics - topics_to_remove)
            removed_count = len(current_topics) - len(remaining_topics)

            if removed_count == 0:
                return {
                    "success": True,
                    "message": "No topics were removed (not found)",
                    "removed": [],
                    "remaining_topics": len(current_topics),
                }

            # Update the interests file
            self._update_section("topics", remaining_topics)

            return {
                "success": True,
                "message": f"Removed {removed_count} topics",
                "removed": list(topics_to_remove & current_topics),
                "remaining_topics": len(remaining_topics),
            }

        except Exception as e:
            self.logger.error(f"Failed to remove topics: {e}")
            return {
                "success": False,
                "error": str(e),
                "removed": [],
                "remaining_topics": 0,
            }

    def update_style(self, style: str) -> Dict:
        """
        Update the summary style preference.

        Args:
            style: New summary style (brief, detailed, technical)

        Returns:
            Dict: Result with success status
        """
        valid_styles = ["brief", "detailed", "technical"]
        if style not in valid_styles:
            return {
                "success": False,
                "error": f"Invalid style '{style}'. Must be one of: {', '.join(valid_styles)}",
                "style": style,
            }

        try:
            # Read current file content
            with open(self.interests_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Update style line
            updated_content = re.sub(r"(- Style: )\w+", f"\\1{style}", content)

            # Update timestamp
            updated_content = re.sub(
                r"Last Updated: .+",
                f'Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                updated_content,
            )

            # Write back atomically
            self._write_file_atomically(updated_content)

            return {
                "success": True,
                "message": f"Updated summary style to '{style}'",
                "style": style,
            }

        except Exception as e:
            self.logger.error(f"Failed to update style: {e}")
            return {"success": False, "error": str(e), "style": style}

    def _update_section(self, section: str, items: List[str]) -> None:
        """
        Update a specific section in the interests file.

        Args:
            section: Section name (topics, sources, notes)
            items: List of items for the section
        """
        with open(self.interests_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Create the new section content
        section_items = "\n".join(f"- {item}" for item in items)

        # Section mapping
        section_headers = {
            "topics": "## Topics",
            "sources": "## Preferred Sources",
            "notes": "## Notes",
        }

        header = section_headers.get(section, f"## {section.title()}")

        # Update the section
        pattern = f"({re.escape(header)}\\s*\\n).*?(?=\\n## |\\n$)"
        replacement = f"\\1<!-- Add your {section} of interest, one per line -->\\n{section_items}\\n"

        updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        # Update timestamp
        updated_content = re.sub(
            r"Last Updated: .+",
            f'Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            updated_content,
        )

        # Write back atomically
        self._write_file_atomically(updated_content)

    def _write_file_atomically(self, content: str) -> None:
        """
        Write content to file atomically using a temporary file.

        Args:
            content: Content to write to the file
        """
        temp_file = self.interests_file.with_suffix(".tmp")

        try:
            # Write to temporary file
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(content)

            # Atomic move
            temp_file.replace(self.interests_file)
            self.logger.debug(f"Successfully updated {self.interests_file}")

        except Exception as e:
            # Clean up temp file on error
            if temp_file.exists():
                temp_file.unlink()
            raise e

    def get_file_path(self) -> str:
        """
        Get the path to the interests.md file.

        Returns:
            str: Absolute path to interests.md
        """
        return str(self.interests_file.absolute())

    def backup_interests(self) -> Dict:
        """
        Create a backup of the current interests file.

        Returns:
            Dict: Result with backup file path
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.data_dir / f"interests_backup_{timestamp}.md"

            if self.interests_file.exists():
                # Copy current file to backup
                with open(self.interests_file, "r", encoding="utf-8") as src:
                    content = src.read()

                with open(backup_file, "w", encoding="utf-8") as dst:
                    dst.write(content)

                return {
                    "success": True,
                    "backup_file": str(backup_file),
                    "timestamp": timestamp,
                }
            else:
                return {
                    "success": False,
                    "error": "No interests file to backup",
                    "backup_file": None,
                }

        except Exception as e:
            self.logger.error(f"Failed to backup interests: {e}")
            return {"success": False, "error": str(e), "backup_file": None}
