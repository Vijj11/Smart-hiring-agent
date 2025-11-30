# Quick API Setup Guide 🚀

## Get Job Search API Keys in 5 Minutes

### ⚡ Fastest Option: Adzuna API (Free)

**1. Go to:** https://developer.adzuna.com/

**2. Click "Sign Up"** and create an account

**3. After login, click "Create New App"**
   - App Name: `Smart Hiring Suite`
   - Select your country
   - Click "Create"

**4. Copy your credentials:**
   - **Application ID** → This is your `ADZUNA_APP_ID`
   - **Application Key** → This is your `ADZUNA_APP_KEY`

**5. Add to `.env` file:**
   ```env
   ADZUNA_APP_ID=abc123def456
   ADZUNA_APP_KEY=xyz789uvw012
   ```

**6. Restart your backend server** ✅

**Done!** You now have 1,000 free API calls per month.

---

### 📋 Optional: SerpAPI (Google Jobs)

**1. Go to:** https://serpapi.com/

**2. Click "Sign Up Free"**

**3. After login, go to Dashboard**

**4. Copy your API Key**

**5. Add to `.env` file:**
   ```env
   SERPAPI_KEY=your_key_here
   ```

**Done!** You now have 100 free searches per month.

---

## 📝 Complete .env Example

```env
# Adzuna (Free - Recommended)
ADZUNA_APP_ID=your_app_id_from_adzuna
ADZUNA_APP_KEY=your_app_key_from_adzuna

# SerpAPI (Optional - Free tier available)
SERPAPI_KEY=your_serpapi_key

# OpenAI (Optional - for better matching)
OPENAI_API_KEY=your_openai_key

# Database (Already configured)
DATABASE_URL=sqlite:///./data/smart_hiring.db
VECTOR_DB=chroma
CHROMA_DIR=./chroma
```

---

## ✅ Test Your Setup

1. **Start your backend:**
   ```bash
   uvicorn backend.app:app --reload --port 8000
   ```

2. **Request job recommendations** in the frontend

3. **Check backend logs** - you should see:
   ```
   INFO - Fetched X jobs from Adzuna
   ```

---

## ❓ Troubleshooting

**"No jobs found"**
- ✅ Check that you added the keys to `.env` correctly
- ✅ Restart the backend server after adding keys
- ✅ Check for typos (no extra spaces!)

**"API key not working"**
- ✅ Make sure you copied the entire key (they're long!)
- ✅ No quotes needed in `.env` file
- ✅ Check Adzuna dashboard to verify keys are active

---

## 💡 Pro Tips

- **Start with Adzuna only** - it's free and easiest
- **SerpAPI is optional** - add later if needed
- **No keys needed?** System works with local jobs only!
- **Free tier limits:**
  - Adzuna: 1,000 requests/month
  - SerpAPI: 100 searches/month

---

## 📚 Need More Details?

See `HOW_TO_GET_API_KEYS.md` for detailed step-by-step instructions with screenshots guidance.

---

**That's it!** Your system will now automatically fetch jobs from external APIs when needed! 🎉

