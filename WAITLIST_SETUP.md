# WhisperForge Waitlist Setup 🌌

Beautiful, standalone waitlist page for early access signups.

## 🚀 Quick Setup

### 1. Database Setup
Run this SQL in your Supabase SQL editor:
```sql
-- Copy and paste from scripts/setup_waitlist_table.sql
```

### 2. Environment Variables
Ensure your `.env` file has:
```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 3. Run Standalone Waitlist
```bash
# Run the standalone waitlist page
streamlit run waitlist.py

# Or access via main app
streamlit run app.py
# Then click "Join the Waitlist" on login page
```

## 📧 Email Sharing

### Option 1: Standalone Page
Deploy `waitlist.py` separately for a clean, distraction-free experience:
- Share URL: `https://your-waitlist-domain.com`
- Perfect for email campaigns and social media

### Option 2: Main App Integration
Access via main app at: `https://your-main-app.com/?page=waitlist`
- Seamlessly integrated with existing auth flow
- Users can sign up or login from same page

## 🎨 Customization

### Brand Colors (in waitlist.py)
```css
--aurora-primary: #00FFFF;        /* Main brand color */
--aurora-secondary: #40E0D0;      /* Secondary accent */
--aurora-tertiary: #7DF9FF;       /* Highlight color */
```

### Content Updates
1. **Tagline**: Line 152 in `waitlist.py`
2. **Description**: Line 156 in `waitlist.py`
3. **Features**: Lines 161-185 in `waitlist.py`
4. **Stats**: Line 265 in `waitlist.py`

### Contact Information
Update email and links in footer (lines 273-280).

## 📊 Analytics & Management

### View Signups
```sql
-- View all waitlist signups
SELECT email, name, interest_level, created_at 
FROM waitlist 
ORDER BY created_at DESC;

-- Count by interest level
SELECT interest_level, COUNT(*) 
FROM waitlist 
GROUP BY interest_level;
```

### Export for Email Marketing
```sql
-- High interest signups for first wave
SELECT email, name 
FROM waitlist 
WHERE interest_level = 'high' 
ORDER BY created_at ASC;
```

## 🔒 Security Notes

- RLS (Row Level Security) enabled
- Anyone can INSERT (for signups)
- Only admins can SELECT (view data)
- Email uniqueness enforced
- No sensitive data collected

## 🚀 Deployment Options

### Streamlit Cloud
1. Push `waitlist.py` to GitHub
2. Deploy via Streamlit Cloud
3. Add environment variables in dashboard

### Railway/Render
1. Create new service
2. Connect GitHub repo
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `streamlit run waitlist.py --server.port $PORT`

### Custom Domain
Point your domain to the deployed waitlist for professional URLs:
- `join.whisperforge.ai`
- `waitlist.yourcompany.com`

## ✅ Testing Checklist

- [ ] Database table created
- [ ] Environment variables set
- [ ] Email validation working
- [ ] Duplicate email handling
- [ ] Success/error messages
- [ ] Mobile responsive design
- [ ] Aurora animations working
- [ ] Form clears after submission

---

**Ready to collect those signups!** 🎉

The waitlist page is designed to be beautiful, fast, and conversion-optimized with the Aurora bioluminescent theme. 