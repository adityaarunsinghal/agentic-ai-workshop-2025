import asyncio
from datetime import datetime

from fast_agent import FastAgent, RequestParams

# Create the application
fast = FastAgent("Newspaper Creation Agent")


# Define the agent with comprehensive news sources
@fast.agent(
    instruction=f"""You are a sophisticated news AI agent with access to multiple news sources and newspaper creation tools.
    Current date and time: {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p %Z')}
    You have access to:
    - **Custom Newspaper Creation**: Full editorial suite for creating personalized newspapers
    - **Content Fetching**: Extract full article content from URLs
    - **Search**: Brave search and Perplexity for research and verification
    Use these tools to:
    1. Create comprehensive, well-researched newspapers
    2. Aggregate news from multiple authoritative sources
    3. Cross-reference stories across different outlets
    4. Build research memory for future reference
    5. Deliver personalized news experiences
    Always cite sources and provide diverse perspectives when possible.
    You may also have the perplexity or brave tools search for specific topics to dive deep or verify information as needed, which you
    can use in tandem with the fetch tool to get full articles.""",
    name="News Agent",
    servers=[
        # Our custom newspaper creation server
        "news_agent_server",
        "fetch",  # Content fetching and extraction
        "brave",  # Web search
        "perplexity_mcp",  # AI-powered research
    ],
    request_params=RequestParams(
        max_iterations=9999,
    ),
)
async def main():
    async with fast.run() as agent:
        await agent.interactive()


if __name__ == "__main__":
    asyncio.run(main())
