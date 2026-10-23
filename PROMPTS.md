# AI Prompts & Refinements Log - TrustVault

### AI Tools Used:
- Google AI Studio / Gemini & ChatGPT for architecture planning and Flask code structure.

### Where AI Got It Wrong & How I Fixed It:
1. **Theme Inconsistency:**
   - AI initially generated templates with bright neon and yellow accents instead of the required cybersecurity palette.
   - **Fix:** Manually enforced dark charcoal (#0B0F0D, #111915) and emerald green (#10B981) tokens across all templates.

2. **Jinja2 Template Syntax Errors:**
   - The AI generated long templates where closing tags (`{% endif %}`) got mismatched or truncated during rendering.
   - **Fix:** Refactored `dashboard.html` to remove fragile nested tags, ensuring clean and robust template rendering.

3. **Overcomplicated Initial Architecture:**
   - AI initially suggested enterprise microservices and unnecessary configurations.
   - **Fix:** Streamlined the design into a clean, monolithic Flask structure with SQLite and isolated file storage.