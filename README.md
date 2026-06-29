# FitCritic

FitCritic is an AI-powered fashion critique web application. Users can describe or upload a photo of their outfit and receive structured, editorial styling feedback along with real product recommendations sourced from the web.

## Features
- **AI Fashion Critique:** Powered by Claude (Anthropic), providing sharp, direct, and structured feedback on your outfit.
- **Image Upload:** Upload photos of your outfit directly in the chat interface.
- **Web Search Integration:** AI automatically searches for and suggests real, shoppable fashion items to elevate your look.
- **Chat History:** Seamlessly resume past styling sessions.
- **Saved Looks:** Bookmark AI feedback that you want to remember or purchase later.
- **Responsive Design:** Dark, minimal, editorial design using Tailwind CSS that looks great on mobile and desktop.

## Tech Stack
- **Backend:** Django 4.x, SQLite
- **Frontend:** Django Templates, Vanilla JavaScript, Tailwind CSS (via CDN)
- **AI:** Anthropic Claude API (`claude-3-5-sonnet-20241022`)
- **Web Search:** DuckDuckGo Search API

## Setup Instructions

1. **Clone or navigate to the project directory**
2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure Environment Variables:**
   Update the `.env` file in the root directory with your keys:
   ```env
   ANTHROPIC_API_KEY=your_anthropic_api_key
   DJANGO_SECRET_KEY=your_django_secret_key
   DEBUG=True
   ```
5. **Run Migrations:**
   ```bash
   python manage.py migrate
   ```
6. **Start the Development Server:**
   ```bash
   python manage.py runserver
   ```
7. Visit `http://127.0.0.1:8000/` in your browser.
