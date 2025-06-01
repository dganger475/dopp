# DoppleGänger

## Overview
DoppleGänger is a full-stack web application for social discovery, face matching, and historical doppelgänger exploration. Users can register, upload photos, find matches, interact with posts, and connect with others in a secure, modern environment.

---

## Features
- User registration, authentication, and profile management
- Face upload, matching, and historical doppelgänger discovery
- Social feed with posts, comments, likes, and notifications
- Search and discover users and matches
- Admin dashboard and moderation tools
- Responsive frontend (React + Vite)
- RESTful API (Flask)
- SQLite database (default, can be swapped for Postgres/MySQL)
- Dockerized for easy deployment
- Caching, rate limiting, and security best practices

---

## Directory Structure

```
Dopp/
├── app.py                # Flask app factory
├── run.py                # Main entry point
├── config.py             # App configuration
├── requirements.txt      # Python dependencies
├── Dockerfile            # Docker build file
├── docker-compose.yml    # Docker Compose config
├── models/               # SQLAlchemy models (User, Post, Comment, etc.)
├── routes/               # Flask blueprints (auth, social, api, etc.)
├── forms/                # WTForms definitions
├── utils/                # Utility modules (db, cache, image, etc.)
├── services/             # Service layer (business logic)
├── static/               # Static files (images, CSS, JS)
├── templates/            # Jinja2 templates
├── tests/                # Pytest test suite
├── migrations/           # Alembic migrations
├── frontend/             # React frontend (see below)
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── components/
│       ├── feedpage/
│       ├── loginpage/
│       ├── profilepage/
│       ├── edit_profile_new/
│       ├── searchPage/
│       ├── welcomepage/
│       ├── registrationpage/
│       ├── notificationspage/
│       ├── comparisonpage/
│       └── ...
└── ...
```

---

## Setup & Installation

### Prerequisites
- Python 3.9+
- Node.js 18+
- (Optional) Docker & Docker Compose

### Backend Setup
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env  # Edit as needed
python run.py  # or flask run
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev  # For development
```

---

## Environment Variables & Configuration
- See `.env.example` for all available settings.
- Key variables:
  - `SECRET_KEY`, `SQLALCHEMY_DATABASE_URI`, `UPLOAD_FOLDER`, etc.
- For production, set secure values and use a production-ready database.

---

## Running the App

### Development
- Backend: `python run.py` or `flask run`
- Frontend: `cd frontend && npm run dev`
- Visit: [http://localhost:5173](http://localhost:5173) (frontend)

### Production
- Use `gunicorn` or `uwsgi` for backend
- Use `npm run build` and serve `frontend/dist` with Nginx or similar
- Or use Docker:
  ```bash
  docker-compose up --build
  ```

---

## Testing
- Backend: `pytest tests/`
- Frontend: `cd frontend && npm test`

---

## Deployment
- Docker and Docker Compose supported out of the box
- Nginx config provided for static/frontend serving
- Environment variables control production settings
- See `docker-compose.yml` and `nginx.conf` for examples

---

## Contributing
1. Fork the repo and create a feature branch
2. Write clear, well-documented code
3. Add/maintain tests
4. Open a pull request with a detailed description

---

## Troubleshooting & FAQ
- **Database issues:** Ensure `faces.db` is present and migrations are up to date
- **CORS errors:** Check backend CORS config and frontend API base URL
- **Static files not loading:** Ensure Nginx/static config is correct
- **Login/auth issues:** Check session/cookie settings and browser console
- **For more help:** See `debug_output.txt` or open an issue

---

## Credits
**Developed by ReaL KeeD**

Special thanks to all contributors, testers, and the open-source community.

---

## License
This project is licensed under the MIT License. See `LICENSE` for details.

## Image URL Normalization Flow

To ensure all face images display correctly across the app (feed, search, etc.), DoppleGänger uses a shared normalization utility:

- **Backend:**
  - All face image URLs are generated using `normalize_extracted_face_path(filename)` from `utils/image_paths.py`.
  - This ensures images are always returned as `/static/extracted_faces/<filename>` (or a valid static path), regardless of their original location or how they're stored in the database.
  - This normalization is applied in:
    - The social feed API (for posts/matches)
    - The search API (for search results)

**Flow Diagram:**

```mermaid
flowchart TD
    A[Face filename in DB] --> B[normalize_extracted_face_path]
    B --> C[/static/extracted_faces/filename]
    C --> D[Returned in API JSON]
    D --> E[Frontend displays image]
```

- This approach prevents broken images and ensures consistency between the feed, search, and all other parts of the app.

---

## Technical Documentation

### Application Architecture

#### Backend (Flask)

##### Blueprints & Routes

1. **Main Blueprint** (`routes/main.py`)
   - `/` - Home page
   - `/about` - About page
   - `/contact` - Contact page

2. **Auth Blueprint** (`routes/auth.py`)
   - `/auth/register` - User registration
   - `/auth/login` - User login
   - `/auth/logout` - User logout
   - `/auth/reset-password` - Password reset
   - `/api/csrf-token` - CSRF token generation

3. **API Blueprint** (`routes/api.py`)
   - `/api/current_user` - Get current user data
   - `/api/profile/data` - Get profile data
   - `/api/stats/followers` - Get follower count
   - `/api/stats/following` - Get following count
   - `/api/search` - Search functionality
   - `/api/social/feed/` - Social feed
   - `/api/social/feed/create_post` - Create post
   - `/api/social/feed/like_post/<post_id>` - Like/unlike post
   - `/api/social/notifications/unread_count` - Get unread notifications

4. **Mobile API Blueprint** (`routes/mobile_api.py`)
   - `/mobile_api/auth/login` - Mobile login
   - `/mobile_api/auth/register` - Mobile registration
   - `/mobile_api/ping` - API health check

5. **Profile Blueprint** (`routes/profile/`)
   - `/profile/view` - View profile
   - `/profile/edit` - Edit profile
   - `/profile/update` - Update profile
   - `/profile/api/user` - Profile API

6. **Face Blueprint** (`routes/face.py`)
   - `/face/upload` - Face upload
   - `/face/match` - Face matching
   - `/face/search` - Face search

7. **Social Blueprint** (`routes/social.py`)
   - `/social/feed` - Social feed
   - `/social/post` - Post management
   - `/social/comment` - Comment management
   - `/social/like` - Like management

8. **Search Blueprint** (`routes/search.py`)
   - `/search` - Search interface
   - `/search/api` - Search API

9. **Admin Blueprint** (`routes/admin.py`)
   - `/admin/dashboard` - Admin dashboard
   - `/admin/users` - User management
   - `/admin/moderate` - Content moderation

##### Database Models

1. **User Model** (`models/user.py`)
   ```python
   class User(UserMixin, db.Model):
       id = db.Column(db.Integer, primary_key=True)
       username = db.Column(db.String(80), unique=True)
       email = db.Column(db.String(120), unique=True)
       password_hash = db.Column(db.String(128))
       # ... other fields
   ```

2. **Face Model** (`models/face.py`)
   ```python
   class Face:
       id = db.Column(db.Integer, primary_key=True)
       filename = db.Column(db.String(200))
       encoding = db.Column(db.BLOB)
       # ... other fields
   ```

3. **Social Models** (`models/social/`)
   - `Post` - Social posts
   - `Comment` - Post comments
   - `Like` - Post likes
   - `Notification` - User notifications
   - `ClaimedProfile` - Claimed face profiles

4. **UserMatch Model** (`models/user_match.py`)
   ```python
   class UserMatch:
       id = db.Column(db.Integer, primary_key=True)
       user_id = db.Column(db.Integer)
       match_filename = db.Column(db.String(200))
       # ... other fields
   ```

#### Frontend (React + Vite)

##### Components Structure

1. **Core Components** (`frontend/src/components/`)
   - `Navbar.jsx` - Navigation bar
   - `Footer.jsx` - Footer
   - `Button.jsx` - Reusable button
   - `Input.jsx` - Form input
   - `Modal.jsx` - Modal dialog
   - `Loading.jsx` - Loading spinner
   - `ErrorBoundary.jsx` - Error handling

2. **Page Components** (`frontend/src/pages/`)
   - `WelcomePage.jsx` - Landing page
   - `LoginPage.jsx` - Login form
   - `RegisterPage.jsx` - Registration form
   - `ProfilePage.jsx` - User profile
   - `EditProfilePage.jsx` - Profile editing
   - `FeedPage.jsx` - Social feed
   - `SearchPage.jsx` - Search interface
   - `NotificationsPage.jsx` - Notifications
   - `ComparisonPage.jsx` - Face comparison

3. **Feature Components** (`frontend/src/features/`)
   - `FaceUpload.jsx` - Face upload
   - `FaceMatch.jsx` - Face matching
   - `Post.jsx` - Post display
   - `Comment.jsx` - Comment system
   - `Like.jsx` - Like functionality
   - `Search.jsx` - Search functionality

4. **Layout Components** (`frontend/src/layouts/`)
   - `MainLayout.jsx` - Main layout
   - `AuthLayout.jsx` - Auth pages layout
   - `ProfileLayout.jsx` - Profile pages layout

##### State Management

1. **Context Providers**
   - `AuthContext` - Authentication state
   - `UserContext` - User data
   - `NotificationContext` - Notifications
   - `ThemeContext` - UI theme

2. **Custom Hooks**
   - `useAuth` - Authentication hooks
   - `useProfile` - Profile management
   - `useFeed` - Feed management
   - `useSearch` - Search functionality

##### API Integration

1. **API Services** (`frontend/src/services/`)
   - `auth.js` - Authentication API
   - `user.js` - User API
   - `face.js` - Face matching API
   - `social.js` - Social features API
   - `search.js` - Search API

2. **API Utilities**
   - `api.js` - Base API configuration
   - `interceptors.js` - Request/response interceptors
   - `error-handling.js` - Error handling

### Data Flow

1. **Authentication Flow**
   ```mermaid
   sequenceDiagram
       User->>Frontend: Enter credentials
       Frontend->>Backend: POST /auth/login
       Backend->>Database: Verify credentials
       Backend->>Frontend: JWT token
       Frontend->>LocalStorage: Store token
   ```

2. **Face Matching Flow**
   ```mermaid
   sequenceDiagram
       User->>Frontend: Upload photo
       Frontend->>Backend: POST /face/upload
       Backend->>FaceModel: Process face
       Backend->>Database: Store encoding
       Backend->>Frontend: Match results
   ```

3. **Social Feed Flow**
   ```mermaid
   sequenceDiagram
       User->>Frontend: Load feed
       Frontend->>Backend: GET /api/social/feed
       Backend->>Database: Fetch posts
       Backend->>Frontend: Post data
       Frontend->>User: Display feed
   ```

### Security Features

1. **Authentication**
   - JWT-based authentication
   - CSRF protection
   - Password hashing
   - Session management

2. **Authorization**
   - Role-based access control
   - Route protection
   - API endpoint security

3. **Data Protection**
   - Input sanitization
   - SQL injection prevention
   - XSS protection
   - File upload security

### Performance Optimizations

1. **Backend**
   - Database indexing
   - Query optimization
   - Caching (Redis)
   - Rate limiting

2. **Frontend**
   - Code splitting
   - Lazy loading
   - Image optimization
   - Caching strategies

### Error Handling

1. **Backend**
   - Global error handlers
   - Custom error responses
   - Logging system
   - Database error handling

2. **Frontend**
   - Error boundaries
   - Toast notifications
   - Form validation
   - API error handling

### Testing Strategy

1. **Backend Tests**
   - Unit tests (pytest)
   - Integration tests
   - API tests
   - Database tests

2. **Frontend Tests**
   - Component tests (Jest)
   - Integration tests
   - E2E tests (Cypress)
   - API mocking

### Deployment

1. **Development**
   - Local development setup
   - Hot reloading
   - Debug tools
   - Development database

2. **Production**
   - Docker containers
   - Nginx reverse proxy
   - SSL/TLS
   - Database backups

### Monitoring & Maintenance

1. **Logging**
   - Application logs
   - Error logs
   - Access logs
   - Performance metrics

2. **Monitoring**
   - Health checks
   - Performance monitoring
   - Error tracking
   - User analytics

This documentation provides a comprehensive overview of the DoppleGänger application's architecture, components, and functionality. For more detailed information about specific components or features, please refer to the respective module's documentation or source code.

---

