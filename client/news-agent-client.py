import asyncio

from fast_agent import FastAgent

# Create the application
fast = FastAgent("Newspaper Creation Agent")


# Define the agent with comprehensive news sources
@fast.agent(
    #     instruction=f"""You are a sophisticated news AI agent with access to multiple news sources and newspaper creation tools.
    # Current date and time: {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p %Z')}
    # You have access to:
    # - **Custom Newspaper Creation**: Full editorial suite for creating personalized newspapers
    # - **Content Fetching**: Extract full article content from URLs
    # - **Search**: Brave search and Perplexity for research and verification
    # Use these tools to:
    # 1. Create comprehensive, well-researched newspapers
    # 2. Aggregate news from multiple authoritative sources
    # 3. Cross-reference stories across different outlets
    # 4. Build research memory for future reference
    # 5. Deliver personalized news experiences
    # Always cite sources and provide diverse perspectives when possible.""",
    name="News Agent",
    servers=[
        # "news_agent_server",
        "agent_server",  # Our custom newspaper creation server
        "fetch",  # Content fetching and extraction
        # "brave",  # Web search
        # "perplexity_mcp",  # AI-powered research
        # "filesystem",
    ],
)
async def main():
    async with fast.run() as agent:
        await agent.interactive()


if __name__ == "__main__":
    asyncio.run(main())
