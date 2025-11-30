# Job API Configuration Guide

The Smart Hiring Suite can fetch jobs dynamically from external APIs when local job postings are insufficient. This guide explains how to configure and use these APIs.

## Supported Job APIs

### 1. Adzuna API (Recommended - Free Tier Available)

Adzuna provides a free tier that allows fetching job listings.

**Setup:**
1. Sign up at https://developer.adzuna.com/
2. Create an application to get your App ID and App Key
3. Add to your `.env` file:
   ```
   ADZUNA_APP_ID=your_app_id_here
   ADZUNA_APP_KEY=your_app_key_here
   ```

**Limits:**
- Free tier: 1000 requests/month
- Rate limit: 10 requests/second

### 2. SerpAPI (Google Jobs Search)

SerpAPI allows you to search Google Jobs programmatically.

**Setup:**
1. Sign up at https://serpapi.com/
2. Get your API key from the dashboard
3. Add to your `.env` file:
   ```
   SERPAPI_KEY=your_serpapi_key_here
   ```

**Limits:**
- Free tier: 100 searches/month
- Paid plans available for more searches

### 3. RapidAPI Job Search (Optional)

If you want to use RapidAPI for job searches:

1. Sign up at https://rapidapi.com/
2. Subscribe to a job search API
3. Add to your `.env` file:
   ```
   RAPIDAPI_KEY=your_rapidapi_key_here
   ```

## How It Works

1. **Local Jobs First**: The system first searches your local database for job matches
2. **API Fallback**: If insufficient local jobs are found, it automatically fetches jobs from configured APIs
3. **Smart Matching**: External jobs are matched against the candidate profile using:
   - Vector similarity search
   - LLM-based re-ranking (if OpenAI API key is configured)
   - Skill extraction and matching

## Configuration Example

Complete `.env` configuration for job APIs:

```env
# Required for LLM features (optional - system works without it)
OPENAI_API_KEY=your_openai_key_here

# Job APIs (optional - system works with local jobs only)
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
SERPAPI_KEY=your_serpapi_key

# Database
DATABASE_URL=sqlite:///./data/smart_hiring.db
VECTOR_DB=chroma
CHROMA_DIR=./chroma
```

## Usage

No special configuration needed! The system automatically:
- Uses local jobs if available
- Fetches from APIs if needed
- Combines results intelligently
- Shows source badge (🌐) for external API jobs in the UI

## Notes

- **No API Keys Required**: The system works perfectly with just local job postings. External APIs are optional enhancements.
- **Privacy**: External jobs are not stored in your database by default (only used for recommendations)
- **Rate Limits**: Be aware of API rate limits when using external services
- **Cost**: Some APIs have free tiers, others require paid subscriptions

## Troubleshooting

**No jobs found:**
- Ensure you have job postings in your local database, OR
- Configure at least one external API (Adzuna recommended)

**API errors:**
- Check your API keys are correct
- Verify you haven't exceeded rate limits
- Check API service status

**Slow recommendations:**
- External API calls add latency
- Consider caching API results
- Use local jobs when possible

