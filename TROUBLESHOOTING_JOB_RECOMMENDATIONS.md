# Troubleshooting: No Job Recommendations Found

If you're seeing "No job recommendations found", here's how to fix it:

## Quick Fixes

### 1. Check Backend Logs

When you request job recommendations, check your backend terminal for messages like:
- `"Only X local jobs found. Fetching from external APIs..."`
- `"Fetched X jobs from external APIs"`
- `"No job API keys configured"`

This will tell you what's happening.

### 2. Ensure You Have Local Jobs OR API Keys

**Option A: Add Local Jobs**
```bash
python -m utils.load_sample_jobs
```

**Option B: Configure External APIs** (Free)
- See `QUICK_API_SETUP.md` for quick setup
- Get Adzuna API keys (5 minutes, free tier)

### 3. Verify API Keys in .env

Make sure your `.env` file has:
```env
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
```

Then **restart your backend server**.

## Common Issues & Solutions

### Issue: "No jobs found" even with API keys

**Possible causes:**
1. **API keys not loaded** - Restart backend after adding keys
2. **API rate limit exceeded** - Check your API dashboard
3. **No vector DB** - System will use fallback but may be slower

**Solution:**
- Check backend logs for specific error messages
- Verify API keys are correct (no extra spaces)
- Try the sample jobs loader: `python -m utils.load_sample_jobs`

### Issue: "No similar jobs found" in logs

This means:
- No local jobs in vector DB
- API fetching might be disabled or failing

**Solution:**
- Check if you have local jobs: Check `data/smart_hiring.db`
- Enable API fetching: Add API keys to `.env`
- Check logs for API errors

### Issue: API fetching works but no results

**Possible causes:**
1. Vector matching failing
2. Skills not extracted from resume

**Solution:**
- System has automatic fallback - it should still return jobs
- Check logs for "using simple fallback" messages
- Make sure your resume has skills listed

## Testing

### Test 1: Local Jobs Only
```bash
# Load sample jobs
python -m utils.load_sample_jobs

# Restart backend
# Request recommendations
```

### Test 2: API Jobs
```bash
# Add API keys to .env
# Restart backend
# Request recommendations (should fetch from APIs)
```

### Test 3: Check Logs
Watch your backend terminal for:
```
INFO - Only 0 local jobs found. Fetching from external APIs...
INFO - Fetched X jobs from external APIs
INFO - Generated X total job recommendations
```

## Debug Mode

To see more detailed logs, check your backend output. The system now:
- ✅ Logs when API fetching starts
- ✅ Logs when API keys are missing
- ✅ Logs number of jobs fetched
- ✅ Shows helpful errors

## Still Not Working?

1. **Check backend logs** - Look for ERROR or WARNING messages
2. **Verify resume uploaded** - You need a resume ID
3. **Test API keys directly** - Try a simple curl request
4. **Check .env file** - Make sure keys are correct format

## Next Steps

1. ✅ Check logs for specific errors
2. ✅ Try loading sample jobs: `python -m utils.load_sample_jobs`
3. ✅ Configure API keys (see `QUICK_API_SETUP.md`)
4. ✅ Restart backend after any changes

---

**The system now has better error handling and will show you exactly what's wrong in the logs!**

