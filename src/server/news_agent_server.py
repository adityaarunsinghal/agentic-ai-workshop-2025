"""
NEWS AGENT MCP SERVER - SESSION 3 WORKSHOP

⚠️ IMPORTANT: THIS FILE IS AN EXTRACTED AND MODIFIED VERSION ⚠️

This code was extracted from the Session 2, Part 2 notebook
(notebooks/0202_advanced_mcp_smart_tools.ipynb) and adapted for standalone use in Session 3.

ORIGINAL SOURCE:
- Workshop: Agentic AI Workshop 2025
- Session: Session 2, Part 2 (Advanced MCP Smart Tools)
- Notebook: notebooks/0202_advanced_mcp_smart_tools.ipynb

KEY MODIFICATIONS FROM ORIGINAL NOTEBOOK:
1. EXTRACTED: Converted from interactive notebook cells into a standalone MCP server
2. ARCHITECTURE CHANGE: Interests management REMOVED and moved to separate preference_agent
3. HTTP TRANSPORT: Configured to run as HTTP transport server on port 8080 (for workshop use)
4. ENHANCED PROMPTS: Added quality gates and preference learning steps to prompts
5. STANDALONE OPERATION: Can run independently from notebook environment

WHAT THIS SERVER PROVIDES:
- Content discovery with ChromaDB storage
- Newspaper creation and composition with smart defaults
- Editorial polish and formatting with LLM sampling
- Quality validation and delivery via email/HTML
- Smart tools that combine multiple operations in one call
- Resources for context summary, article search, and newspaper archive

For the complete educational context, step-by-step explanations, and the original
implementation, please refer to the original notebook file:
    notebooks/0202_advanced_mcp_smart_tools.ipynb

This standalone version is intended for use in Session 3 as part of the multi-agent
newspaper creation system alongside the preference_agent.
"""

import asyncio
import os
import sys
import warnings
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, List

from dotenv import load_dotenv
from fastmcp import Context, FastMCP

# Load environment
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Add project root to path so we can import from src.server
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Service imports
from src.server.config.settings import get_settings
from src.server.services.article_memory_v2 import ArticleMemoryService
from src.server.services.email_service import EmailService
from src.server.services.http_client import HackerNewsClient, fetch_content
from src.server.services.newspaper_service import NewspaperService

# ============================================================================
# APPLICATION CONTEXT
# ============================================================================


@dataclass
class AppContext:
    """Application context with all services."""

    hn_client: HackerNewsClient
    article_memory: ArticleMemoryService
    newspaper_service: NewspaperService
    email_service: EmailService
    settings: object


@asynccontextmanager
async def app_lifespan(mcp: FastMCP):
    """Initialize all services for the newspaper agent."""
    print("🚀 Starting News Agent MCP Server")

    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    # Initialize services
    hn_client = HackerNewsClient()
    article_memory = ArticleMemoryService()
    article_memory.initialize(settings.data_dir / "chromadb")
    newspaper_service = NewspaperService(settings.data_dir)

    # Email service
    email_service = EmailService(
        {
            "server": "smtp.gmail.com",
            "port": 465,
            "use_tls": False,
            "use_ssl": True,
            "username": os.getenv("MCP_SMTP_FROM_EMAIL", ""),
            "password": os.getenv("MCP_SMTP_PASSWORD", ""),
            "from_email": os.getenv("MCP_SMTP_FROM_EMAIL", ""),
            "from_name": "AI Newspaper Agent",
        }
    )

    print("✅ All services initialized!")

    try:
        yield AppContext(
            hn_client=hn_client,
            article_memory=article_memory,
            newspaper_service=newspaper_service,
            email_service=email_service,
            settings=settings,
        )
    finally:
        print("👋 Shutting down MCP Server")


# ============================================================================
# MCP SERVER
# ============================================================================

mcp = FastMCP(
    name="news-agent-server",
    instructions="""Advanced newspaper creation system with intelligent content discovery and composition.

AGENT ROLE: Strategic Editor
- Decide WHICH stories to cover
- Choose editorial ANGLE and DEPTH
- Control STRUCTURE and POLISH
- Delegate tactical execution to smart tools

SMART FEATURES:
- Content discovery automatically stores in ChromaDB with clean content IDs
- One tool call adds multiple articles with full formatting
- Elicitation enables interactive workflows
- Quality validation enforces standards

CORE WORKFLOW:
1. discover_stories() → Get enriched story list with content IDs
2. quick_look() → Preview any content by ID
3. create_newspaper() → Start with smart defaults
4. add_content_cluster() → Add multiple articles in one call
5. Polish with section/article controls
6. validate_and_finalize() → Enforce quality standards
7. publish_newspaper() → Deliver

Current date: {datetime.now().strftime('%A, %B %d, %Y')}""",
    lifespan=app_lifespan,
)


# ============================================================================
# RESOURCES
# ============================================================================


@mcp.resource("memory://context-summary")
async def get_context_summary(ctx: Context = None) -> str:
    """Live summary of archive - recent newspapers, trending topics, coverage gaps.

    Annotations: High priority, refreshes every 5 minutes."""
    article_memory = ctx.request_context.lifespan_context.article_memory

    # Get stats
    stats = article_memory.get_context_summary()

    content = "# Archive Context Summary\n\n"

    content += "## Recent Activity\n"
    content += f"- **Total Articles Stored:** {stats['total_articles']}\n"
    content += f"- **Newspapers Created:** {stats['total_newspapers']}\n"
    content += f"- **Last Article Added:** {stats['last_article_date']}\n\n"

    if stats["recent_newspapers"]:
        content += "## Recent Newspapers (Last 5)\n"
        for paper in stats["recent_newspapers"]:
            content += f"- **{paper['title']}** ({paper['date']}) - {paper['reading_time']}min, {paper['article_count']} articles\n"
        content += "\n"

    if stats["trending_topics"]:
        content += "## Trending Topics (Most Covered)\n"
        for topic, count in stats["trending_topics"]:
            content += f"- {topic}: {count} articles\n"
        content += "\n"

    return content


@mcp.resource("memory://articles/{topic}")
async def get_articles_by_topic(topic: str, ctx: Context = None) -> str:
    """Dynamic resource template - search articles by topic.

    Example: memory://articles/distributed-systems
    Returns semantic search results for that topic."""
    article_memory = ctx.request_context.lifespan_context.article_memory

    articles = article_memory.search_articles(query=topic, limit=10)

    if not articles:
        return f"# No articles found for '{topic}'\n\nTry broader search terms or different topics."

    content = f"# Articles about '{topic}' ({len(articles)} found)\n\n"

    for i, article in enumerate(articles, 1):
        content += f"## {i}. {article['title']}\n"
        content += f"**Content ID:** {article.get('content_id', 'unknown')}\n"
        content += f"**Similarity:** {article['similarity']:.1%} | "
        content += f"**Source:** {article['source']} | "
        content += f"**Reading Time:** {article.get('reading_time', '?')} min\n"
        if article["topics"]:
            content += f"**Topics:** {', '.join(article['topics'])}\n"
        content += f"**URL:** {article['url']}\n\n"
        if article.get("summary"):
            content += f"{article['summary']}\n\n"
        content += "---\n\n"

    return content


@mcp.resource("memory://newspapers/recent")
async def get_recent_newspapers(ctx: Context = None) -> str:
    """Recent newspapers for structural reference and avoiding repetition.

    Shows last 5 newspapers with structure, topics, and metadata."""
    article_memory = ctx.request_context.lifespan_context.article_memory

    newspapers = article_memory.search_newspapers(days_back=30)[:5]

    if not newspapers:
        return "# No Recent Newspapers\n\nThis is your first newspaper!"

    content = f"# Recent Newspapers ({len(newspapers)})\n\n"

    for paper in newspapers:
        content += f"## {paper['title']}\n"
        content += f"**ID:** {paper['newspaper_id']}\n"
        content += f"**Date:** {paper['timestamp'][:10]}\n"
        content += f"**Type:** {paper['edition_type']} | "
        content += f"**Articles:** {paper['article_count']} | "
        content += f"**Reading Time:** {paper['reading_time']} min\n"
        if paper["topics"]:
            content += f"**Topics:** {', '.join(paper['topics'])}\n"
        if paper.get("tone"):
            content += f"**Tone:** {paper['tone']}\n"

        # Show structure if available
        if paper.get("structure"):
            content += (
                f"**Structure:** {', '.join(paper['structure'].get('sections', []))}\n"
            )

        content += "\n---\n\n"

    return content


# ============================================================================
# TOOLS: CONTENT DISCOVERY
# ============================================================================


@mcp.tool()
async def discover_stories(
    query: str = "tech news",
    count: int = 20,
    sources: List[str] = None,
    ctx: Context = None,
) -> str:
    """
    Discover stories from multiple sources and store with content IDs.

    This is the PRIMARY discovery tool. It:
    1. Fetches stories from sources (HN, web, etc.)
    2. Stores full content in ChromaDB automatically
    3. Generates clean content IDs for easy reference
    4. Returns enriched summaries for decision-making

    Args:
        query: Search query (e.g., "AI ethics", "distributed systems")
        count: Number of stories to fetch (1-30)
        sources: List of sources ["hn", "web", "perplexity"] (default: ["hn"])

    Returns:
        Formatted list of stories with content IDs, titles,
        and metadata. Use content IDs with other tools like quick_look() or
        add_content_cluster().

    Example:
        discover_stories("AI ethics", count=20, sources=["hn", "web"])
        → Returns stories with IDs like cnt_hn_20251005_abc123
    """
    if not 1 <= count <= 30:
        return "❌ Count must be between 1 and 30"

    sources = sources or ["hn"]

    hn_client = ctx.request_context.lifespan_context.hn_client
    article_memory = ctx.request_context.lifespan_context.article_memory

    await ctx.info(f"🔍 Discovering {count} stories from {sources}...")

    enriched_stories = []

    # Fetch from Hacker News
    if "hn" in sources:
        await ctx.report_progress(progress=0, total=count)

        story_ids = await hn_client.get_story_ids("topstories", count)

        for i, story_id in enumerate(story_ids):
            story: dict[str, Any] = await hn_client.get_item(story_id)
            if not story or not story.get("title"):
                continue

            await ctx.report_progress(progress=i + 1, total=count)

            # Generate content ID
            url = story.get("url", "")
            hash_value = abs(hash(url)) % 10000
            content_id = f"cnt_hn_{datetime.now().strftime('%Y%m%d')}_{hash_value:04d}"

            # Fetch full content and capture final URL after redirects
            try:
                full_content, final_url = await fetch_content(url, max_length=8000)
                # Use final URL after redirects instead of original
                url = final_url
            except:
                full_content = story.get("title", "")
                # Keep original URL if fetch fails

            # Store in ChromaDB
            await ctx.debug(f"Storing content_id: {content_id}")
            article_memory.store_article_with_content_id(
                content_id=content_id,
                url=url,
                content=full_content,
                title=story["title"],
                source="hn",
                topics=[],
                summary="",
            )

            # Search for related past articles
            related = article_memory.search_articles(query=story["title"], limit=3)

            enriched_stories.append(
                {
                    "content_id": content_id,
                    "title": story["title"],
                    "url": url,
                    "source": "hn",
                    "score": story.get("score", 0),
                    "word_count": len(full_content.split()),
                    "estimated_reading_time": max(1, len(full_content.split()) // 200),
                    "related_past_articles": [a["title"] for a in related],
                }
            )

    # Sort by score
    enriched_stories.sort(key=lambda x: x["score"], reverse=True)

    # Format output
    result = f"# 📰 Discovered {len(enriched_stories)} Stories\n\n"
    result += f"**Query:** {query}\n"
    result += f"**Sources:** {', '.join(sources)}\n"
    result += "**Sorted by:** HN Score\n\n"

    for i, story in enumerate(enriched_stories, 1):
        result += f"## {i}. {story['title']}\n"
        result += f"**Content ID:** `{story['content_id']}`\n"
        result += f"**Reading Time:** {story['estimated_reading_time']}min | "
        result += f"**HN Score:** {story['score']}\n"
        if story["related_past_articles"]:
            result += f"**Related Past Coverage:** {len(story['related_past_articles'])} articles\n"
        result += f"**URL:** {story.get('url', 'N/A')}\n\n"

    await ctx.info(f"✅ Discovered and stored {len(enriched_stories)} stories")

    return result


@mcp.tool()
async def quick_look(content_ids: List[str], ctx: Context = None) -> str:
    """
    Quick preview of stored content by content ID.

    Use this to review content before adding to newspaper.
    Shows title, metadata, and first 300 characters.

    Args:
        content_ids: List of content IDs to preview

    Returns:
        Compact preview of each content item

    Example:
        quick_look(["cnt_hn_20251005_1234", "cnt_hn_20251005_5678"])
    """
    article_memory = ctx.request_context.lifespan_context.article_memory

    previews = []
    for content_id in content_ids:
        article = article_memory.get_by_content_id(content_id)

        if article:
            previews.append(article)
        else:
            previews.append({"content_id": content_id, "error": "Not found"})

    # Format output
    result = f"# 👀 Quick Look: {len(content_ids)} items\n\n"

    for preview in previews:
        if "error" in preview:
            result += f"## ❌ {preview['content_id']}\n"
            result += f"**Error:** {preview['error']}\n\n"
            continue

        result += f"## {preview['title']}\n"
        result += f"**Content ID:** `{preview['content_id']}`\n"
        result += f"**Word Count:** {preview['word_count']} | "
        result += f"**Reading Time:** {preview.get('reading_time', '?')}min\n"
        if preview.get("topics"):
            result += f"**Topics:** {', '.join(preview['topics'])}\n"
        result += f"\n**Preview:**\n{preview['content_preview']}\n\n"
        result += "---\n\n"

    return result


# ============================================================================
# TOOLS: NEWSPAPER CREATION
# ============================================================================


@mcp.tool()
async def create_newspaper(
    title: str,
    type: str = "deep_dive",
    subtitle: str = "",
    structure_template: str = None,
    ctx: Context = None,
) -> str:
    """
    Create new newspaper with smart defaults.

    Sets up newspaper structure based on type with pre-configured sections
    and target reading times.

    Args:
        title: Newspaper title
        type: Edition type - determines structure and targets
              - "morning_brief": 2 sections, 15min target
              - "deep_dive": 3-4 thematic sections, 35min target
              - "thematic": Custom sections, agent-driven
              - "follow_up": Timeline + Analysis, 20min target
        subtitle: Optional subtitle
        structure_template: Optional newspaper_id to copy structure from

    Returns:
        Newspaper ID and configuration details
    """
    newspaper_service = ctx.request_context.lifespan_context.newspaper_service

    # Type-specific defaults
    type_configs = {
        "morning_brief": {
            "sections": ["Breaking News", "Quick Reads"],
            "target_reading_time": 15,
            "suggested_articles": 7,
        },
        "deep_dive": {
            "sections": ["Topic 1", "Topic 2", "Topic 3"],
            "target_reading_time": 35,
            "suggested_articles": 10,
        },
        "thematic": {
            "sections": [],  # Agent will define
            "target_reading_time": 25,
            "suggested_articles": 8,
        },
        "follow_up": {
            "sections": ["What Changed", "Deep Analysis"],
            "target_reading_time": 20,
            "suggested_articles": 6,
        },
    }

    config = type_configs.get(type, type_configs["deep_dive"])

    # Create newspaper
    result = newspaper_service.create_draft(title, subtitle, type)

    if not result["success"]:
        return f"❌ {result.get('error', 'Failed to create newspaper')}"

    newspaper_id = result["newspaper_id"]

    # Add pre-configured sections
    for section_title in config["sections"]:
        newspaper_service.add_section(
            newspaper_id,
            section_title,
            layout="featured" if section_title == config["sections"][0] else "grid",
        )

    # Set metadata
    newspaper_service.set_metadata(
        newspaper_id,
        {
            "target_reading_time": config["target_reading_time"],
            "suggested_articles": config["suggested_articles"],
        },
    )

    await ctx.info(f"✅ Created {type} newspaper: {newspaper_id}")

    response = "# ✅ Created Newspaper\n\n"
    response += f"**ID:** `{newspaper_id}`\n"
    response += f"**Title:** {title}\n"
    response += f"**Type:** {type}\n"
    response += f"**Target Reading Time:** {config['target_reading_time']} minutes\n"
    response += f"**Suggested Articles:** {config['suggested_articles']}\n\n"

    if config["sections"]:
        response += "**Pre-configured Sections:**\n"
        for section in config["sections"]:
            response += f"- {section}\n"

    response += "\n**Next Steps:**\n"
    response += "1. Use add_content_cluster() to add articles\n"
    response += "2. Polish with section/article controls\n"
    response += "3. validate_and_finalize() to check quality\n"
    response += "4. publish_newspaper() to deliver\n"

    return response


@mcp.tool()
async def add_content_cluster(
    newspaper_id: str,
    section: str,
    content_ids: List[str],
    treatment: str = "detailed",
    auto_enhance: bool = True,
    link_related: bool = True,
    ctx: Context = None,
) -> str:
    """
    Add multiple related articles as a coherent cluster - THE WORKHORSE TOOL.

    This tool does EVERYTHING in one call:
    - Fetches content from ChromaDB (already stored by discover_stories)
    - Uses sampling to generate summaries with full context
    - Formats with rich elements (quotes, key points)
    - Links related articles
    - Updates newspaper

    IMPORTANT: If the section already exists, calling this will REPLACE all articles
    in that section. To add multiple sets of articles to the same section, include
    ALL content_ids in a single call. This prevents duplicate sections with the
    same name (e.g., multiple "Breaking News" sections).

    If content_ids > 5, may elicit user preference on depth.

    Args:
        newspaper_id: Target newspaper
        section: Section to add to (replaces existing section if it exists)
        content_ids: List of content IDs to add
        treatment: Summary style
                   - "brief": Quick overview (2-3 sentences)
                   - "detailed": Comprehensive summary (6-8 sentences)
                   - "technical": Focus on technical details
        auto_enhance: Automatically add pull quotes and key points
        link_related: Cross-reference articles in cluster

    Returns:
        Summary of articles added and enhancements applied
    """
    if len(content_ids) == 0:
        return "❌ No content IDs provided"

    article_memory = ctx.request_context.lifespan_context.article_memory
    newspaper_service = ctx.request_context.lifespan_context.newspaper_service

    await ctx.info(f"📝 Adding {len(content_ids)} articles to '{section}'...")

    # Elicit if too many articles
    if len(content_ids) > 5:
        from dataclasses import make_dataclass

        choice_response = await ctx.elicit(
            message=f"Found {len(content_ids)} articles. Include all (comprehensive) or top 5 (focused)?",
            response_type=make_dataclass("SelectionChoice", [("selection", str)]),
        )

        if (
            choice_response.action == "accept"
            and choice_response.data.selection == "focused"
        ):
            content_ids = content_ids[:5]
            await ctx.info("📊 User selected focused approach - using top 5 articles")

    # Fetch all articles from ChromaDB
    articles = []
    for content_id in content_ids:
        article = article_memory.get_by_content_id(content_id)
        if article:
            articles.append(article)
        else:
            await ctx.warning(f"Content ID not found: {content_id}")

    if not articles:
        return "❌ No valid articles found"

    await ctx.report_progress(progress=0, total=len(articles))

    # Process each article
    added_articles = []
    total_reading_time = 0

    for i, article in enumerate(articles):
        await ctx.debug(f"Processing: {article['title']}")

        # Find related past coverage
        related = article_memory.search_articles(query=article["content"], limit=5)

        # Use sampling to generate summary
        await ctx.info(f"🤖 Generating {treatment} summary with LLM...")

        sample_result = await ctx.sample(
            messages=[
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"""Summarize this article in {treatment} style.

PAST COVERAGE (for context):
{chr(10).join(f"- {r['title']}" for r in related[:3])}

ARTICLE TO SUMMARIZE:
Title: {article["title"]}
Content: {article["content"]}

Provide a {treatment} summary that acknowledges past coverage when relevant.""",
                    },
                }
            ],
            temperature=0.3,
            max_tokens=500 if treatment == "brief" else 1000,
        )

        summary = sample_result.text

        # Auto-enhance if requested
        pull_quote = ""
        key_points = []

        if auto_enhance:
            await ctx.info("✨ Extracting pull quote and key points...")

            # Extract pull quote
            quote_result = await ctx.sample(
                messages=[
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": f"Extract the single most impactful quote from this article (15-30 words):\n\n{article['content'][:2000]}",
                        },
                    }
                ],
                temperature=0.2,
                max_tokens=100,
            )
            pull_quote = quote_result.text

            # Extract key points
            points_result = await ctx.sample(
                messages=[
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": f"Extract 3-5 key points from this article as a bullet list:\n\n{article['content'][:2000]}",
                        },
                    }
                ],
                temperature=0.2,
                max_tokens=300,
            )
            points_text = points_result.text
            key_points = [
                line.strip("- ").strip()
                for line in points_text.split("\n")
                if line.strip().startswith("-")
            ]

        # Add to newspaper
        result = newspaper_service.add_article(
            newspaper_id=newspaper_id,
            section_title=section,
            article_data={
                "title": article["title"],
                "content": summary,
                "url": article["url"],
                "source": article["source"],
                "tags": article.get("topics", []),
            },
            placement="lead" if i == 0 else "standard",
        )
        if not result["success"]:
            return result["error"]

        # Apply formatting
        result = newspaper_service.set_article_format(
            newspaper_id=newspaper_id,
            section_title=section,
            article_title=article["title"],
            format_options={"pull_quote": pull_quote, "key_points": key_points},
        )
        if not result["success"]:
            return result["error"]

        added_articles.append(article["title"])
        total_reading_time += article.get("reading_time", 1)

        await ctx.report_progress(progress=i + 1, total=len(articles))

    # Link related if requested
    if link_related and len(added_articles) > 1:
        for i, title in enumerate(added_articles):
            related_titles = [t for j, t in enumerate(added_articles) if j != i]
            newspaper_service.link_related_articles(
                newspaper_id=newspaper_id,
                article_title=title,
                related_titles=related_titles[:3],  # Max 3 links
            )

    await ctx.info(f"✅ Added {len(added_articles)} articles to '{section}'")

    result = "# ✅ Content Cluster Added\n\n"
    result += f"**Section:** {section}\n"
    result += f"**Articles Added:** {len(added_articles)}\n"
    result += f"**Reading Time Added:** ~{total_reading_time} minutes\n"
    result += f"**Treatment:** {treatment}\n\n"

    result += "**Articles:**\n"
    for title in added_articles:
        result += f"- {title}\n"

    if auto_enhance:
        result += "\n**Enhancements Applied:**\n"
        result += "- Pull quotes extracted\n"
        result += "- Key points identified\n"

    if link_related:
        result += "- Related articles cross-referenced\n"

    return result


@mcp.tool()
async def create_editorial_synthesis(
    newspaper_id: str,
    content_ids: List[str],
    angle: str = "analytical",
    placement: str = "section_intro",
    ctx: Context = None,
) -> str:
    """
    Generate editorial content connecting multiple stories using sampling.

    Uses LLM to synthesize insights across articles with full context from
    past coverage.

    Args:
        newspaper_id: Target newspaper
        content_ids: Stories to synthesize
        angle: Editorial perspective
               - "analytical": Objective analysis with implications
               - "educational": Explain concepts with context
               - "skeptical": Question assumptions, highlight concerns
               - "forward-looking": Future trends and predictions
        placement: Where to place
                   - "section_intro": Introduction to section
                   - "theme_bridge": Connect different topics
                   - "closing_thoughts": Wrap-up perspective

    Returns:
        Confirmation of editorial added
    """
    article_memory = ctx.request_context.lifespan_context.article_memory
    newspaper_service = ctx.request_context.lifespan_context.newspaper_service

    await ctx.info(f"✍️ Generating {angle} editorial...")

    # Fetch articles
    articles = []
    for content_id in content_ids:
        article = article_memory.get_by_content_id(content_id)
        if article:
            articles.append(article)

    if not articles:
        return "❌ No valid articles found"

    # Prepare context
    articles_summary = "\n\n".join(
        [f"Article: {a['title']}\nContent: {a['content'][:500]}..." for a in articles]
    )

    # Generate editorial
    await ctx.info("🤖 Generating editorial with LLM...")

    angle_instructions = {
        "analytical": "Provide objective analysis with insights and implications",
        "educational": "Explain concepts clearly with context for learning",
        "skeptical": "Question assumptions and highlight potential concerns",
        "forward-looking": "Identify future trends and make predictions",
    }

    sample_result = await ctx.sample(
        messages=[
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": f"""Write a {angle} editorial connecting these stories (300-400 words).

{angle_instructions[angle]}

STORIES TO CONNECT:
{articles_summary}

Write an editorial that synthesizes these stories into a coherent narrative.""",
                },
            }
        ],
        temperature=0.7,
        max_tokens=600,
    )

    editorial = sample_result.text

    # Add to newspaper
    newspaper_service.add_editors_note(
        newspaper_id=newspaper_id,
        content=editorial,
        placement=placement,
        style="highlighted",
    )

    await ctx.info(f"✅ Editorial added with {angle} perspective")

    return f"✅ Editorial synthesis added\n\n**Angle:** {angle}\n**Placement:** {placement}\n**Stories Connected:** {len(articles)}"


# ============================================================================
# TOOLS: POLISH & EDITORIAL CONTROL
# ============================================================================


@mcp.tool()
async def set_section_style(
    newspaper_id: str, section: str, layout: str = "grid", ctx: Context = None
) -> str:
    """
    Control section visual presentation.

    Args:
        newspaper_id: Target newspaper
        section: Section to style
        layout: Layout type
                - "featured": One big article, rest smaller
                - "grid": Equal-sized grid layout
                - "timeline": Timeline with chronological flow
                - "single-column": Single column for long-form
    """
    newspaper_service = ctx.request_context.lifespan_context.newspaper_service

    result = newspaper_service.set_section_layout(newspaper_id, section, layout)

    if result["success"]:
        return f"✅ Set '{section}' to {layout} layout"
    else:
        return f"❌ {result['error']}"


@mcp.tool()
async def enhance_article(
    newspaper_id: str,
    section: str,
    article_title: str,
    add_pull_quote: bool = False,
    add_key_points: bool = False,
    ctx: Context = None,
) -> str:
    """
    Add polish to specific article using LLM extraction.

    Args:
        newspaper_id: Target newspaper
        section: Section containing article
        article_title: Article to enhance
        add_pull_quote: Extract compelling quote
        add_key_points: Extract key takeaways
    """
    newspaper_service = ctx.request_context.lifespan_context.newspaper_service

    # Get article content
    newspaper_data = newspaper_service.get_newspaper_data(newspaper_id)
    if not newspaper_data:
        return "❌ Newspaper not found"

    # Find article
    article = None
    for s in newspaper_data["sections"]:
        if s["title"] == section:
            for a in s["articles"]:
                if a["title"] == article_title:
                    article = a
                    break

    if not article:
        return "❌ Article not found"

    enhancements = {}

    # Extract pull quote if requested
    if add_pull_quote:
        await ctx.info("✨ Extracting pull quote...")
        quote_result = await ctx.sample(
            messages=[
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"Extract the most compelling quote from this article (15-30 words):\n\n{article['content']}",
                    },
                }
            ],
            temperature=0.2,
            max_tokens=100,
        )
        enhancements["pull_quote"] = quote_result.text

    # Extract key points if requested
    if add_key_points:
        await ctx.info("✨ Extracting key points...")
        points_result = await ctx.sample(
            messages=[
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"Extract 3-5 key points from this article as a bullet list:\n\n{article['content']}",
                    },
                }
            ],
            temperature=0.2,
            max_tokens=300,
        )
        points_text = points_result.text
        enhancements["key_points"] = [
            line.strip("- ").strip()
            for line in points_text.split("\n")
            if line.strip().startswith("-")
        ]

    # Apply enhancements
    newspaper_service.set_article_format(
        newspaper_id=newspaper_id,
        section_title=section,
        article_title=article_title,
        format_options=enhancements,
    )

    return f"✅ Enhanced '{article_title}' with {len(enhancements)} enhancements"


@mcp.tool()
async def reorder_and_emphasize(
    newspaper_id: str,
    section: str,
    article_order: List[str],
    highlights: dict = None,
    ctx: Context = None,
) -> str:
    """
    Control narrative flow and emphasis within section.

    Args:
        newspaper_id: Target newspaper
        section: Section to reorder
        article_order: List of article titles in desired order
        highlights: Dict mapping article title to highlight type
                    - "breaking": Breaking news badge
                    - "exclusive": Exclusive content badge
                    - "trending": Trending badge
                    - "deep-dive": Deep dive badge
    """
    newspaper_service = ctx.request_context.lifespan_context.newspaper_service

    # Get section
    newspaper_data = newspaper_service.get_newspaper_data(newspaper_id)
    if not newspaper_data:
        return "❌ Newspaper not found"

    section_data = None
    for s in newspaper_data["sections"]:
        if s["title"] == section:
            section_data = s
            break

    if not section_data:
        return f"❌ Section '{section}' not found"

    # Reorder articles
    current_articles = {a["title"]: a for a in section_data["articles"]}
    reordered = []

    for title in article_order:
        if title in current_articles:
            reordered.append(current_articles[title])
        else:
            return f"❌ Article '{title}' not found in section"

    section_data["articles"] = reordered

    # Apply highlights
    highlights = highlights or {}
    for article_title, highlight_type in highlights.items():
        newspaper_service.highlight_article(
            newspaper_id=newspaper_id,
            section_title=section,
            article_title=article_title,
            highlight_type=highlight_type,
        )

    # Save changes
    newspaper_service._save_draft(newspaper_id, newspaper_data)

    return f"✅ Reordered {len(article_order)} articles in '{section}' with {len(highlights)} highlights"


@mcp.tool()
async def add_editorial_element(
    newspaper_id: str,
    element_type: str,
    placement: str = "top",
    content: str = "",
    generate: bool = False,
    generation_context: str = "",
    ctx: Context = None,
) -> str:
    """
    Add editorial elements (notes, highlights, etc).

    Can either use provided content OR generate using LLM.

    Args:
        newspaper_id: Target newspaper
        element_type: Type of element
                      - "editors_note": Editor's commentary
                      - "theme_highlight": Connect cross-theme stories
                      - "stats_callout": Highlight key statistics
        placement: Where to place ("top", "bottom", or "section:<name>")
        content: Content to use (if not generating)
        generate: If True, use LLM to generate content
        generation_context: Context for generation (e.g., "Connect privacy and performance themes")
    """
    newspaper_service = ctx.request_context.lifespan_context.newspaper_service

    # Generate content if requested
    if generate and generation_context:
        await ctx.info(f"🤖 Generating {element_type} content...")

        newspaper_data = newspaper_service.get_newspaper_data(newspaper_id)

        sample_result = await ctx.sample(
            messages=[
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"""Generate a {element_type} for a newspaper.

Context: {generation_context}

Newspaper Title: {newspaper_data.get("title", "")}
Sections: {", ".join(s["title"] for s in newspaper_data.get("sections", []))}

Write 2-3 sentences appropriate for a {element_type}.""",
                    },
                }
            ],
            temperature=0.6,
            max_tokens=200,
        )

        content = sample_result.text

    # Add element based on type
    if element_type == "editors_note":
        newspaper_service.add_editors_note(
            newspaper_id=newspaper_id,
            content=content,
            placement=placement,
            style="highlighted",
        )
    elif element_type == "theme_highlight":
        newspaper_service.add_theme_highlight(
            newspaper_id=newspaper_id,
            theme=generation_context.split()[0] if generation_context else "Theme",
            description=content,
            related_articles=[],
        )
    else:
        return f"❌ Unsupported element type: {element_type}"

    return f"✅ Added {element_type} at {placement}"


# ============================================================================
# TOOLS: QUALITY CONTROL & DELIVERY
# ============================================================================


@mcp.tool()
async def preview_newspaper(
    newspaper_id: str, preview_type: str = "summary", ctx: Context = None
) -> str:
    """
    Preview newspaper with different analysis views.

    Args:
        newspaper_id: Newspaper to preview
        preview_type: Type of preview
                      - "summary": Stats and metadata
                      - "structure": Section breakdown
                      - "full": Complete markdown
    """
    newspaper_service = ctx.request_context.lifespan_context.newspaper_service
    email_service = ctx.request_context.lifespan_context.email_service

    if preview_type in ["summary", "structure"]:
        result = newspaper_service.get_stats(newspaper_id)
        if not result["success"]:
            return f"❌ {result['error']}"

        stats = result["stats"]
        output = "# 📊 Newspaper Summary\n\n"
        output += f"**Title:** {stats['title']}\n"
        output += f"**Type:** {stats['edition_type']}\n"
        output += f"**Articles:** {stats['total_articles']}\n"
        output += f"**Reading Time:** {stats['total_reading_time']} minutes\n"
        output += f"**Sections:** {stats['section_count']}\n\n"

        output += "**Section Breakdown:**\n"
        for section in stats["sections"]:
            output += f"- {section['title']} ({section['layout']}): {section['article_count']} articles\n"

        return output
    elif preview_type == "full":
        newspaper_data = newspaper_service.get_newspaper_data(newspaper_id)
        if not newspaper_data:
            return "❌ Newspaper not found"
        return email_service._create_text_version(newspaper_data)
    return "❌ Preview type not fully implemented yet"


@mcp.tool()
async def validate_and_finalize(
    newspaper_id: str,
    min_reading_time: int = None,
    min_articles: int = None,
    ctx: Context = None,
) -> str:
    """
    Validate newspaper meets quality standards with ENFORCEMENT.

    Unlike old design, this PREVENTS publication if standards not met
    and provides actionable fixes.

    Args:
        newspaper_id: Newspaper to validate
        min_reading_time: Minimum reading time in minutes (optional)
        min_articles: Minimum number of articles (optional)

    Returns:
        Validation results with actionable fixes if needed
    """
    newspaper_service = ctx.request_context.lifespan_context.newspaper_service

    await ctx.info("🔍 Validating newspaper quality...")

    # Get newspaper data
    newspaper_data = newspaper_service.get_newspaper_data(newspaper_id)
    if not newspaper_data:
        return "❌ Newspaper not found"

    # Check basic validation
    result = newspaper_service.validate(newspaper_id)

    issues = []
    warnings = []

    # Check custom requirements
    current_reading_time = newspaper_data["metadata"]["total_reading_time"]
    current_articles = newspaper_data["metadata"]["article_count"]

    if min_reading_time and current_reading_time < min_reading_time:
        shortfall = min_reading_time - current_reading_time
        issues.append(
            {
                "type": "reading_time",
                "current": current_reading_time,
                "required": min_reading_time,
                "suggestion": f"Add {shortfall // 3} more detailed articles (~3min each)",
                "fix": f"Use add_content_cluster() with {shortfall // 3} content IDs and treatment='detailed'",
            }
        )

    if min_articles and current_articles < min_articles:
        shortfall = min_articles - current_articles
        issues.append(
            {
                "type": "article_count",
                "current": current_articles,
                "required": min_articles,
                "suggestion": f"Add {shortfall} more articles",
                "fix": f"Use add_content_cluster() with {shortfall} content IDs",
            }
        )

    # Check for empty sections
    for section in newspaper_data["sections"]:
        if not section["articles"]:
            warnings.append(f"Section '{section['title']}' is empty")

    # Combine with basic validation
    all_issues = result.get("issues", []) + [i["type"] for i in issues]
    all_warnings = result.get("warnings", []) + warnings

    # Format output
    if not all_issues:
        output = "# ✅ Newspaper Valid!\n\n"
        output += "All quality standards met. Ready to publish.\n\n"

        if all_warnings:
            output += "**Warnings:**\n"
            for warning in all_warnings:
                output += f"⚠️ {warning}\n"

        return output
    else:
        output = "# ❌ Newspaper Needs Improvement\n\n"

        output += "**Issues Found:**\n"
        for issue in issues:
            output += f"\n**{issue['type'].replace('_', ' ').title()}**\n"
            output += f"- Current: {issue['current']}\n"
            output += f"- Required: {issue['required']}\n"
            output += f"- Suggestion: {issue['suggestion']}\n"
            output += f"- Fix: `{issue['fix']}`\n"

        if all_warnings:
            output += "\n**Warnings:**\n"
            for warning in all_warnings:
                output += f"⚠️ {warning}\n"

        output += "\n**Cannot publish until issues resolved.**\n"

        return output


@mcp.tool()
async def publish_newspaper(
    newspaper_id: str, delivery_method: str = "email", ctx: Context = None,
) -> str:
    """
    Finalize and deliver newspaper.

    Args:
        newspaper_id: Newspaper to publish
        delivery_method: How to deliver
                         - "email": Send via email
                         - "save_html": Save HTML locally
                         - "both": Email and save
    """
    newspaper_service = ctx.request_context.lifespan_context.newspaper_service
    email_service = ctx.request_context.lifespan_context.email_service
    article_memory = ctx.request_context.lifespan_context.article_memory
    settings = ctx.request_context.lifespan_context.settings

    await ctx.info("📰 Publishing newspaper...")

    # Get newspaper data
    newspaper_data = newspaper_service.get_newspaper_data(newspaper_id)
    if not newspaper_data:
        return "❌ Newspaper not found"

    # Generate HTML
    await ctx.report_progress(progress=0, total=3)
    html_content = email_service._create_html_version(newspaper_data)

    # Save HTML
    html_file = settings.data_dir / "newspapers" / f"{newspaper_id}.html"
    html_file.parent.mkdir(parents=True, exist_ok=True)
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    await ctx.report_progress(progress=1, total=3)

    # Send email if requested
    email_sent = False
    if delivery_method in ["email", "both"]:
        result = email_service.send_newspaper(newspaper_data, version=2)
        email_sent = result["success"]
        if not email_sent:
            await ctx.warning(f"Email failed: {result.get('error', 'Unknown error')}")

    await ctx.report_progress(progress=2, total=3)

    # Store in archive
    article_memory.store_newspaper(newspaper_id, newspaper_data)

    await ctx.report_progress(progress=3, total=3)
    await ctx.info("✅ Newspaper published and archived")

    # Format output
    output = "# ✅ Newspaper Published!\n\n"
    output += f"**Title:** {newspaper_data['title']}\n"
    output += f"**Articles:** {newspaper_data['metadata']['article_count']}\n"
    output += f"**Reading Time:** {newspaper_data['metadata']['total_reading_time']} minutes\n\n"

    if email_sent:
        output += "📧 **Email:** Sent successfully\n"

    if delivery_method in ["save_html", "both"] or not email_sent:
        output += f"💾 **HTML:** Saved to {html_file}\n"

    output += "🗄️ **Archive:** Stored in memory\n"

    return output


# ============================================================================
# TOOLS: CONTEXT HELPERS
# ============================================================================


@mcp.tool()
async def search_context(
    query: str, context_type: str = "articles", limit: int = 10, ctx: Context = None
) -> str:
    """
    Search archive for relevant context.

    Args:
        query: Search query
        context_type: What to search
                      - "articles": Search article archive
                      - "newspapers": Search past newspapers
                      - "topics": Search by topic
        limit: Maximum results (1-20)
    """
    article_memory = ctx.request_context.lifespan_context.article_memory

    if context_type == "articles":
        articles = article_memory.search_articles(query=query, limit=limit)

        if not articles:
            return f"No articles found for '{query}'"

        result = f"# 🔍 Found {len(articles)} Articles\n\n"
        for i, article in enumerate(articles, 1):
            result += f"## {i}. {article['title']}\n"
            result += f"**Content ID:** {article.get('content_id', 'unknown')}\n"
            result += f"**Similarity:** {article['similarity']:.1%}\n"
            result += f"**Source:** {article['source']}\n\n"

        return result

    elif context_type == "newspapers":
        newspapers = article_memory.search_newspapers(days_back=90, query=query)

        if not newspapers:
            return f"No newspapers found for '{query}'"

        result = f"# 🔍 Found {len(newspapers)} Newspapers\n\n"
        for paper in newspapers:
            result += f"## {paper['title']}\n"
            result += f"**Date:** {paper['timestamp'][:10]}\n"
            result += f"**Type:** {paper['edition_type']}\n"
            result += f"**Articles:** {paper['article_count']}\n\n"

        return result

    else:
        return f"❌ Unsupported context type: {context_type}"


@mcp.tool()
async def get_related_content(
    content_id: str,
    relationship_type: str = "similar",
    limit: int = 5,
    ctx: Context = None,
) -> str:
    """
    Find content related to a specific article.

    Args:
        content_id: Content ID to find relations for
        relationship_type: Type of relationship
                           - "similar": Similar content
                           - "follow_up": Follow-up coverage
                           - "background": Background context
        limit: Maximum results (1-20)
    """
    article_memory = ctx.request_context.lifespan_context.article_memory

    # Get base article
    article = article_memory.get_by_content_id(content_id)
    if not article:
        return f"❌ Content ID not found: {content_id}"

    # Search for related
    related = article_memory.search_articles(query=article["content"], limit=limit)

    # Filter out the original article
    related = [r for r in related if r.get("content_id") != content_id]

    if not related:
        return f"No related content found for '{article['title']}'"

    result = f"# 🔗 Related to: {article['title']}\n\n"
    result += f"**Relationship Type:** {relationship_type}\n"
    result += f"**Found:** {len(related)} related articles\n\n"

    for i, rel in enumerate(related, 1):
        result += f"## {i}. {rel['title']}\n"
        result += f"**Content ID:** {rel.get('content_id', 'unknown')}\n"
        result += f"**Similarity:** {rel['similarity']:.1%}\n"
        result += f"**Source:** {rel['source']}\n\n"

    return result


# ============================================================================
# PROMPTS
# ============================================================================


@mcp.prompt()
async def create_morning_brief() -> str:
    """Workflow for creating a quick morning newspaper (15-20min read)."""
    return """Create a focused morning tech brief (15-20min read)

WORKFLOW:
0. Understand User Preferences (REQUIRED FIRST STEP):
   Search your available tools for preference validation or user preference capabilities.
   Consult these to understand the user's interests, topics they care about, and reading patterns.
   Use this information to guide story selection throughout the workflow.

1. discover_stories(query="tech news today", count=20, sources=["hn"])
   → Review summaries, pick top stories aligned with user preferences

2. create_newspaper(type="morning_brief", title=f"Morning Brief - {date}")

3. add_content_cluster(
     newspaper_id,
     section="Breaking News",
     content_ids=[top 3 content_ids],
     treatment="brief",
     auto_enhance=True
   )

4. add_content_cluster(
     newspaper_id,
     section="Quick Reads",
     content_ids=[next 4-5 content_ids],
     treatment="brief"
   )

5. preview_newspaper(newspaper_id, preview_type="full")

6. Quality Gate - Review for Personalization (REQUIRED):
    Search your available tools for content review or preference validation capabilities.
    Submit the FULL newspaper content for review against user preferences and patterns.
    This is a REQUIRED quality gate before finalization - do not skip.
    Only proceed if the review is approved.

7. Preference Learning (REQUIRED):
    Extract the main topics covered in this newspaper (e.g., "AI/ML", "Emacs", "Swift", "Developer Tools").

    Use your available tools to propose storing these topics for future personalization.
    The system may ask for user confirmation before storing - wait for any prompts.

    CRITICAL: Wait for any confirmation dialogs and responses before proceeding.

8. validate_and_finalize(
     newspaper_id,
     min_reading_time=5,
     min_articles=5
   )

9. publish_newspaper(delivery_method="email")

TOOL CALLS: ~7-9
AGENT CONTROLS: Which stories, final polish, topic selection"""


@mcp.prompt()
async def create_deep_dive() -> str:
    """Workflow for comprehensive deep dive newspaper (30-45min read)."""
    return """Create comprehensive deep dive newspaper (30-45min read)

WORKFLOW:
0. Understand User Preferences (REQUIRED FIRST STEP):
   Search your available tools for preference validation or user preference capabilities.
   Consult these to understand the user's interests, topics they care about, and reading patterns.
   Use this information to guide story selection throughout the workflow.

1. discover_stories(query="tech", count=30, sources=["hn"])
   → Review enriched summaries with relevance scores, prioritizing user interests

2. Review resource: memory://context-summary
   → Check trending topics and coverage gaps

3. Group stories by theme (use your judgment based on topics)

4. create_newspaper(type="deep_dive", title="Deep Dive: {themes}")

5. For each theme (3-4 themes):
   a. add_content_cluster(
        newspaper_id,
        section=theme_name,
        content_ids=[3-4 content_ids],
        treatment="detailed",
        auto_enhance=True,
        link_related=True
      )
      → Tool handles: fetch, context, sampling, formatting

   b. enhance_article(
        newspaper_id,
        section=theme_name,
        article_title=lead_article,
        add_pull_quote=True,
        add_key_points=True
      )
      → Extra polish for lead article

   c. create_editorial_synthesis(
        newspaper_id,
        content_ids=theme_content_ids,
        angle="analytical",
        placement="section_intro"
      )

6. If themes connect:
   add_editorial_element(
     newspaper_id,
     element_type="theme_highlight",
     generate=True,
     generation_context="Connect cross-theme patterns"
   )

7. preview_newspaper(newspaper_id, preview_type="full")

8. Quality Gate - Review for Personalization (REQUIRED):
    Search your available tools for content review or preference validation capabilities.
    Submit the FULL newspaper content for review against user preferences and patterns.
    This is a REQUIRED quality gate before finalization - do not skip.
    Only proceed if the review is approved.

9. Preference Learning (REQUIRED):
    Extract the main topics covered in this newspaper (e.g., "AI/ML", "Emacs", "Swift", "Developer Tools").

    Use your available tools to propose storing these topics for future personalization.
    The system may ask for user confirmation before storing - wait for any prompts.

    CRITICAL: Wait for any confirmation dialogs and responses before proceeding.

10. validate_and_finalize(
     newspaper_id,
     min_reading_time=30,
     min_articles=8
   )
   → If fails: Get specific fixes, execute, re-validate

11. publish_newspaper(delivery_method="both")

TOOL CALLS: ~20-25
AGENT CONTROLS: Theme selection, lead articles, editorial angles, cross-theme synthesis
DELEGATED: Content fetching, summarization, formatting, context inclusion"""


@mcp.prompt()
async def follow_story() -> str:
    """Follow up on story from past newspapers."""
    return """Follow up on story from past newspapers

WORKFLOW:
0. Understand User Preferences (REQUIRED FIRST STEP):
   Search your available tools for preference validation or user preference capabilities.
   Consult these to understand the user's interests, topics they care about, and reading patterns.
   Use this information to guide story selection throughout the workflow.

1. search_context(query=topic, context_type="newspapers")
   → Identify past coverage

2. Read resource: memory://articles/{topic}
   → See all related past articles

3. discover_stories(query=topic, count=15, sources=["hn"])
   → Find new developments

4. get_related_content(content_id=original_story, relationship_type="follow_up")

5. create_newspaper(
     type="follow_up",
     title=f"Follow-up: {topic}",
     structure_template=past_newspaper_id
   )

6. add_content_cluster(
     newspaper_id,
     section="What Changed",
     content_ids=new_developments,
     treatment="detailed"
   )

7. add_content_cluster(
     newspaper_id,
     section="Deep Analysis",
     content_ids=analysis_pieces,
     treatment="technical"
   )

8. create_editorial_synthesis(
     newspaper_id,
     content_ids=[all],
     angle="forward-looking",
     placement="closing_thoughts"
   )

9. Quality Gate - Review for Personalization (REQUIRED):
    Search your available tools for content review or preference validation capabilities.
    Submit the FULL newspaper content for review against user preferences and patterns.
    This is a REQUIRED quality gate before finalization - do not skip.
    Only proceed if the review is approved.

10. Preference Learning (REQUIRED):
    Extract the main topics covered in this newspaper (e.g., "AI/ML", "Emacs", "Swift", "Developer Tools").

    Use your available tools to propose storing these topics for future personalization.
    The system may ask for user confirmation before storing - wait for any prompts.

    CRITICAL: Wait for any confirmation dialogs and responses before proceeding.

11. validate_and_finalize + publish_newspaper

TOOL CALLS: ~15-20
AGENT CONTROLS: What's "new" vs rehash, comparative emphasis, predictions"""


# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    print("\n" + "=" * 60)
    print("🚀 NEWS AGENT MCP SERVER")
    print("=" * 60)
    print("\n📊 Server Statistics:")
    print("  • Resources: 3 (context summary, articles by topic, recent newspapers)")
    print("  • Tools: 14 (discovery, creation, polish, quality, context)")
    print("  • Prompts: 3 (morning brief, deep dive, follow story)")
    print("\n✨ Key Features:")
    print("  • Smart composition - one tool does many operations")
    print("  • Content IDs - clean references for agents")
    print("  • Sampling - LLM generation for summaries & editorials")
    print("  • Elicitation - interactive user choices")
    print("  • Progress - real-time operation updates")
    print("  • Quality enforcement - prevents low-quality newspapers")
    print("\n" + "=" * 60 + "\n")

    # Run server: bind to all interfaces so it's reachable from containers and host
    print("🌐 Binding MCP HTTP server to 0.0.0.0:8080 (path: /mcp)")
    asyncio.run(
        mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=8080,
        )
    )
