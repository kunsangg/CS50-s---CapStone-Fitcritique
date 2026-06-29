# FitCritic

FitCritic is an AI-powered fashion critique web application. Users describe or upload a photo of their outfit and receive structured, editorial-quality styling feedback from an AI fashion critic — including a fit score, detailed observations, actionable suggestions, and product recommendations. The interface is designed to feel like a premium AI chat tool, not a typical student project.

---

## Distinctiveness and Complexity

FitCritic is meaningfully distinct from every other project in CS50W, and its complexity goes well beyond what any of those projects required.

**Why it is not Project 2 (Commerce):** Project 2 is an auction-based e-commerce platform. FitCritic has no products for sale, no listings, no bidding, no shopping cart, and no transactions of any kind. The "Product Picks" section of a critique card surfaces AI-generated suggestions for fashion items — these are text recommendations, not purchasable listings in a database. There is no seller, no buyer, and no commerce flow. The application is a critique and advisory tool, not a marketplace.

**Why it is not Project 4 (Social Network):** Project 4 is a Twitter-like social network with posts, likes, follows, and a feed. FitCritic has none of these. There is no concept of following another user, no public feed of user-generated posts, no social graph. The only content a user sees is their own chat sessions and saved critiques. The application is a personal AI assistant, not a social platform.

**What makes FitCritic genuinely complex:**

The core complexity of FitCritic comes from its AI integration layer and the structured data pipeline it requires. Unlike a simple chatbot wrapper, FitCritic enforces a strict JSON schema on every AI response — fit score, summary, what works, what does not work, suggestions, and product picks — and renders each field as a distinct UI component. This required careful prompt engineering to make the Gemini API reliably return valid, parseable JSON, and a robust cleaning pipeline to handle malformed responses including smart quotes, unterminated strings, and markdown code fences that the model occasionally produces.

The application manages persistent multi-turn conversation history. Every message in a session is stored in the database and reconstructed on each API call so that the AI has full context of the conversation. This is architecturally more complex than a single-turn question-and-answer interface.

Image upload support adds another dimension of complexity. Users can attach outfit photos directly in the chat composer. The image is stored server-side and encoded as base64 before being passed to Gemini's vision capability, which analyzes the visual content of the outfit alongside any text description. Handling multipart form data, file storage, and vision API payloads simultaneously required careful coordination across the view, utility, and frontend layers.

The Style Trends feature integrates the Unsplash API to surface a dynamic, randomized masonry grid of fashion photography. Each photo card has a hover interaction that pre-fills the chat composer with a critique prompt, creating a seamless flow from trend discovery to AI critique. This required a secondary API integration, a dedicated backend endpoint, and a custom masonry layout in vanilla JavaScript.

The Saved Critiques feature required designing a many-to-one relationship between users, chat sessions, and individual assistant messages, with a SavedLook join model that links a user to a specific message. The save action is handled asynchronously via a fetch POST, and the Saved Critiques page reconstructs and re-renders the full critique card from the stored JSON without making a new AI call.

The frontend is written entirely in vanilla JavaScript with no frameworks. The chat interface includes optimistic UI updates, a bouncing loading indicator, auto-resizing textarea, image preview with removal, send button state management, and dynamic DOM rendering of structured critique cards — all implemented from scratch without jQuery or React.

---

## Files

### Root
- `manage.py` — Django management entry point
- `requirements.txt` — Python dependencies
- `.env` — Environment variables (not committed; see setup instructions)
- `README.md` — This file

### fitcritic/
- `settings.py` — Django project settings; loads environment variables including `GEMINI_API_KEY`, `UNSPLASH_ACCESS_KEY`, and `DJANGO_SECRET_KEY`
- `urls.py` — Root URL configuration; includes routes from the `core` app
- `wsgi.py` — WSGI entry point for deployment

### core/
- `models.py` — Defines four models: `UserProfile` (extends Django User with avatar and bio), `ChatSession` (a named conversation belonging to a user), `Message` (individual messages within a session, storing role, text content, and optional image), and `SavedLook` (links a user to a specific assistant message they have bookmarked)
- `views.py` — All application views including `index`, `chat_view`, `saved_critiques_view`, `style_trends_view`, and JSON API endpoints: `chat_api` (handles message processing and Gemini calls), `save_look` (saves a critique to SavedLook), `fetch_trends_api` (proxies Unsplash API for fashion photos), and session management endpoints
- `urls.py` — URL patterns for all core views and API endpoints
- `forms.py` — Django forms for user registration and profile editing
- `admin.py` — Registers all models with the Django admin interface

### core/utils/
- `llm.py` — Core AI utility. Builds the Gemini API request payload including conversation history, system prompt, and optional base64-encoded image. Handles the full JSON cleaning pipeline: strips markdown fences, extracts the JSON object by finding the first `{` and last `}`, replaces smart quotes, and falls back gracefully on parse failure. Contains the FitCritic system prompt that enforces structured JSON output.
- `helpers.py` — Helper utilities including session title auto-generation from the first user message

### core/templates/
- `base.html` — Global layout shell with sidebar (New Critique button, navigation links, recent sessions list, user avatar and name at bottom), Inter font via Google Fonts, Tailwind CSS via CDN, and CSRF meta tag
- `index.html` — Landing page with hero background image, FitCritic wordmark, tagline, and suggestion chips that link to the chat
- `chat.html` — Main chat interface; renders message thread and the fixed bottom composer with text input, image upload button, and send button
- `saved.html` — Saved Critiques page; renders a responsive two-column grid of saved critique cards reconstructed from stored JSON
- `trends.html` — Style Trends page; renders a masonry grid of fashion photos from Unsplash with hover-activated critique buttons
- `profile.html` — User profile page with avatar upload and bio editing
- `login.html` — Login form
- `register.html` — Registration form

### core/static/
- `css/app.css` — Custom styles that Tailwind CDN cannot handle: auto-resizing textarea behavior, scrollbar hiding for the message thread, sidebar transition animations, and masonry column layout adjustments
- `js/chat.js` — Full chat interface logic: send on Enter, optimistic user message rendering, fetch POST to `/api/chat/`, loading dots animation, structured critique card DOM rendering (fit score, summary, what works, what does not, suggestions, product picks), async save look handler, image preview and removal, CSRF token extraction, and session ID persistence across turns
- `js/upload.js` — Image file selection handler; shows thumbnail preview above the composer and exposes the selected file to `chat.js`
- `js/ui.js` — Sidebar toggle for mobile (hamburger + overlay), send button color state (gray when empty, indigo when input present), and general UI helpers

---

## How to Run

### Prerequisites
- Python 3.10 or higher
- pip

### Setup

1. Clone the repository:
```
git clone https://github.com/kunsangg/CS50-s---CapStone-Fitcritique.git
cd CS50-s---CapStone-Fitcritique
```

2. Create and activate a virtual environment:
```
python -m venv venv
source venv/bin/activate
# On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following:
```
GEMINI_API_KEY=your_gemini_api_key_here
UNSPLASH_ACCESS_KEY=your_unsplash_access_key_here
DJANGO_SECRET_KEY=your_django_secret_key_here
DEBUG=True
```

To get a Gemini API key: visit [aistudio.google.com](https://aistudio.google.com), sign in, and create a key under API Keys.

To get an Unsplash Access Key: visit [unsplash.com/developers](https://unsplash.com/developers), create a free account, and register a new application.

5. Run migrations:
```
python manage.py migrate
```

6. Start the development server:
```
python manage.py runserver
```

7. Visit `http://127.0.0.1:8000/` in your browser. Register an account to begin.

---

## Additional Notes

- The application uses **Google Gemini 2.0 Flash Lite** via the Gemini REST API. This model supports both text and image (vision) inputs on the free tier.
- The Gemini free tier allows approximately 1,500 requests per day. During heavy testing this limit may be reached, in which case the application surfaces a user-friendly error message in the chat rather than crashing.
- All API keys are loaded from `.env` via `python-dotenv` and are never hardcoded or committed to the repository.
- The `.env` file is listed in `.gitignore` and will not appear in the repository. The grader will need to supply their own API keys using the template above.
- The application is mobile-responsive. The sidebar collapses on screens below 768px and is accessible via a hamburger menu. The chat composer remains pinned to the bottom of the viewport on all screen sizes.
- SQLite is used as the database. No additional database setup is required beyond running migrations.
- No npm, Node.js, or build step is required. Tailwind CSS is loaded via CDN.
