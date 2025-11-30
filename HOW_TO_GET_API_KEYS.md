# How to Get API Keys for Job Search APIs

This guide provides step-by-step instructions for obtaining API keys from supported job search services.

## Option 1: Adzuna API (Recommended - Free Tier)

Adzuna offers a free tier with 1,000 API requests per month.

### Step-by-Step Guide:

1. **Visit the Adzuna Developer Portal**
   - Go to: https://developer.adzuna.com/
   - Click on **"Get Started"** or **"Sign Up"**

2. **Create an Account**
   - Click **"Create Account"** or **"Register"**
   - Fill in your details:
     - Email address
     - Password
     - Name
   - Accept the terms and conditions
   - Click **"Sign Up"**

3. **Verify Your Email**
   - Check your email inbox
   - Click the verification link sent by Adzuna

4. **Create an Application**
   - Once logged in, navigate to **"My Apps"** or **"Applications"**
   - Click **"Create New App"** or **"Add Application"**
   - Fill in the application details:
     - **App Name**: e.g., "Smart Hiring Suite"
     - **Description**: Brief description of your project
     - **Website**: Your website (optional)
   - Select your country (for job search region)
   - Click **"Create"** or **"Save"**

5. **Get Your API Credentials**
   - After creating the app, you'll see:
     - **Application ID** (App ID)
     - **Application Key** (App Key)
   - Copy both values

6. **Add to Your .env File**
   ```env
   ADZUNA_APP_ID=paste_your_app_id_here
   ADZUNA_APP_KEY=paste_your_app_key_here
   ```

### Free Tier Limits:
- ✅ 1,000 API requests per month
- ✅ Access to job listings worldwide
- ✅ No credit card required

### Paid Plans (if needed):
- Starter: $99/month - 10,000 requests
- Pro: $299/month - 50,000 requests

---

## Option 2: SerpAPI (Google Jobs Search)

SerpAPI allows you to search Google Jobs programmatically. They offer a free tier with 100 searches per month.

### Step-by-Step Guide:

1. **Visit SerpAPI Website**
   - Go to: https://serpapi.com/
   - Click **"Sign Up Free"** or **"Get Started"**

2. **Create an Account**
   - Choose a signup method:
     - Sign up with Google (recommended)
     - Sign up with email
   - If using email:
     - Enter your email
     - Create a password
     - Click **"Sign Up"**

3. **Verify Your Email** (if using email signup)
   - Check your inbox
   - Click the verification link

4. **Get Your API Key**
   - After logging in, go to **"Dashboard"**
   - You'll see your **API Key** displayed
   - Click the copy icon to copy it
   - Or go to **"API Keys"** section

5. **Add to Your .env File**
   ```env
   SERPAPI_KEY=paste_your_api_key_here
   ```

### Free Tier Limits:
- ✅ 100 searches per month
- ✅ Access to Google Jobs results
- ✅ No credit card required

### Paid Plans (if needed):
- Hobby: $50/month - 5,000 searches
- Standard: $250/month - 40,000 searches
- Business: Custom pricing

---

## Quick Setup Summary

### Minimum Setup (Free):

1. **Get Adzuna API Keys:**
   - Visit: https://developer.adzuna.com/
   - Sign up → Create App → Copy App ID & Key

2. **Get SerpAPI Key (Optional):**
   - Visit: https://serpapi.com/
   - Sign up → Copy API Key from Dashboard

3. **Update Your .env File:**
   ```env
   # Adzuna API (Recommended)
   ADZUNA_APP_ID=your_app_id_here
   ADZUNA_APP_KEY=your_app_key_here
   
   # SerpAPI (Optional - for Google Jobs)
   SERPAPI_KEY=your_serpapi_key_here
   ```

4. **Restart Your Backend Server:**
   - Stop the backend (Ctrl+C)
   - Start it again: `uvicorn backend.app:app --reload --port 8000`

---

## Testing Your API Keys

After adding the keys, test them by:

1. **Check Backend Logs:**
   - When you request job recommendations, you should see:
   - `INFO - Fetched X jobs from Adzuna`
   - Or `INFO - Fetched X jobs from external APIs`

2. **Test in the Application:**
   - Upload a resume
   - Request job recommendations
   - If external jobs appear, your API keys are working!

---

## Troubleshooting

### Adzuna API Issues:

**Problem**: "Adzuna API credentials not configured"
- **Solution**: Make sure both `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` are in your `.env` file
- Restart the backend server after adding keys

**Problem**: "Failed to fetch from Adzuna: 401 Unauthorized"
- **Solution**: Check that your App ID and App Key are correct
- Make sure there are no extra spaces in your `.env` file

**Problem**: "Rate limit exceeded"
- **Solution**: You've used your monthly free quota (1,000 requests)
- Wait until next month, or upgrade to a paid plan

### SerpAPI Issues:

**Problem**: "SerpAPI key not configured"
- **Solution**: Add `SERPAPI_KEY` to your `.env` file
- This is optional - Adzuna will work without it

**Problem**: "Error fetching via SerpAPI: Invalid API key"
- **Solution**: Verify your API key is correct
- Check your SerpAPI dashboard for the correct key

---

## Alternative: Using Only Local Jobs

If you don't want to use external APIs:
- ✅ The system works perfectly with just local job postings
- ✅ No API keys needed
- ✅ No rate limits
- ✅ Just upload jobs manually or use sample jobs

To add local jobs:
1. Use the sample job loader: `python -m utils.load_sample_jobs`
2. Or add jobs via the API endpoint
3. Or add them directly to the database

---

## Security Best Practices

1. **Never commit your .env file:**
   - Make sure `.env` is in your `.gitignore`
   - Don't share API keys publicly

2. **Use environment variables in production:**
   - Don't hardcode keys in your code
   - Use secure secret management in production

3. **Rotate keys periodically:**
   - Change your API keys every few months
   - Especially if you suspect they've been compromised

---

## Need Help?

- **Adzuna Support**: https://developer.adzuna.com/docs
- **SerpAPI Support**: https://serpapi.com/dashboard
- **Check your backend logs** for detailed error messages

---

## Summary

**Easiest Path (Recommended):**
1. Get Adzuna API keys (free, 5 minutes) → https://developer.adzuna.com/
2. Add to `.env` file
3. Restart backend
4. Done! 🎉

The system will automatically use these APIs when needed!

