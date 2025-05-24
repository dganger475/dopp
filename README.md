# Dopp - Face Matching Application

A modern web application for finding face matches, with a Flask backend and React frontend. The application allows users to register, upload profile images, and find other users or historical images that look similar to them.

## Recent Enhancements (May 2025)

### Search Page UI Improvements
We've recently refactored and enhanced the Search Page component to improve both functionality and user experience:

1. **Modular Component Structure**:
   - Split large SearchPage.jsx into smaller, focused components (CardResult.jsx, LoadingState.jsx, EmptyState.jsx)
   - Improved code maintainability and readability
   - Each component now handles a specific UI element with clear responsibilities

2. **User Card Styling**:
   - Implemented distinct card styles for different user types:
     - User Card: Black background with blue border and blue pills
     - Registered User Cards: Red background with black border, "REGISTERED USER" pill at top, username pill below image
     - Unclaimed Profile Cards: Blue background with black border, "UNCLAIMED PROFILE" pill at top
   - All cards use Arial font and 5.3px borders for visual consistency
   - Added proper card snapping behavior when scrolling in the carousel

3. **Visual Enhancements**:
   - Match percentage badges on cards with color coding based on match strength
   - Visual scroll indicators with right arrow navigation
   - Smooth keyboard navigation using arrow keys
   - Improved loading states with placeholder cards
   - Empty state message when no matches are found

4. **Bug Fixes**:
   - Fixed image display for registered users
   - Ensured usernames properly display for registered users
   - Corrected button positioning and styling
   - Restricted carousel to horizontal scrolling only

### Current Status

The application is functional with the following key features implemented:

- User registration and authentication
- Profile image uploading and processing
- Face matching search functionality
- Enhanced search results UI with visual indicators
- Responsive design for different screen sizes

## For Future Developers

### Architecture Overview
- **Backend**: Flask application with SQLite database (faces.db)
- **Frontend**: React application with component-based architecture
- **Face Matching**: FAISS vector database for efficient similarity searching

### Important Files and Directories
- `/frontend/src/components/` - Reusable UI components
- `/frontend/src/searchPage/` - Search page implementation
- `manual_rebuild_faiss.py` - Script to rebuild the FAISS index

### Styling Guidelines
1. **Card Design**:
   - User Card: Black background with blue border and blue pills
   - Registered User Cards: Red background with black border
   - Unclaimed Profile Cards: Blue background with black border
   - All cards use Arial font and 5.3px borders

2. **Component Structure**:
   - Component files should be focused on a single responsibility
   - Reusable UI elements should be placed in the components directory
   - Page-specific components should be in their respective page directories

### Known Issues and Future Work
1. **Username Display**: There are ongoing issues with displaying usernames for registered users. The current implementation hard-codes "@Profile #103" as a temporary solution.

2. **Image Loading**: The application sometimes has issues loading profile images, particularly for registered users. The current implementation uses error handlers to attempt multiple image sources.

3. **Carousel Navigation**: The horizontal scrolling and card snapping behavior works, but could be improved for smoother transitions.

4. **Data Fetching**: The application could benefit from implementing a more robust data fetching approach, potentially using React Query or similar solutions.

### Development Tips
1. **Console Logging**: Added extensive console logging for debugging username and image issues. Check browser console when making changes to these features.

2. **Testing Changes**: When modifying the Search Page, test with both registered and unregistered users to ensure styling remains consistent.

3. **Mobile Responsiveness**: Ensure any UI changes maintain responsiveness for mobile devices.

## Table of Contents
- [Features](#features)
- [Setup](#setup)
- [Development Tools](#development-tools)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Configuration](#configuration)
- [Security Features](#security-features)
- [Performance Features](#performance-features)
- [Debugging Tools](#debugging-tools)
- [Profiling Tools](#profiling-tools)
- [Mock Data Generation](#mock-data-generation)
- [CLI Commands](#cli-commands)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## Features

### Security
- CSRF protection with customizable settings
- Password complexity requirements and validation
- Rate limiting on sensitive routes
- Secure session management with configurable timeouts
- Secure file upload handling with type validation
- XSS prevention through input sanitization
- Security headers (HSTS, CSP, etc.)
- Input validation and sanitization utilities

### Performance
- Database connection pooling with SQLAlchemy
- Query optimization and monitoring
- Redis caching support with fallback
- Optimized file upload handling
- Image processing improvements
- Request profiling and monitoring

### Development
- Comprehensive testing setup
- Code quality checks
- Pre-commit hooks
- Type checking
- Detailed documentation
- Development utilities package

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. Initialize the development environment:
   ```bash
   flask dev setup-dev
   ```

6. Create mock data (optional):
   ```bash
   flask dev create-mock-data
   ```

7. Run the development server:
   ```bash
   flask run
   ```

## Development Tools

### Debug Utilities (`utils/dev/debug.py`)
- `debug_info()`: Get comprehensive application state information
- `log_request_info`: Decorator for detailed request logging
- `debug_view`: Debug endpoint registration
- `setup_debug_logging`: Configure detailed debug logging

Example usage:
```python
from utils.dev.debug import debug_info, log_request_info

@log_request_info
def my_route():
    state = debug_info()
    return jsonify(state)
```

### Profiling Tools (`utils/dev/profiling.py`)
- `profile_function`: Decorator for function profiling
- `profile_request`: Decorator for request profiling
- `Profiler`: Context manager for code block profiling

Example usage:
```python
from utils.dev.profiling import profile_function, Profiler

@profile_function
def expensive_operation():
    # Your code here
    pass

with Profiler("my-operation"):
    # Code to profile
    pass
```

### Testing Utilities (`utils/dev/testing.py`)
- `MockDataGenerator`: Generate realistic test data
- `create_test_data`: Populate database with test data
- Random data generation utilities

Example usage:
```python
from utils.dev.testing import MockDataGenerator

# Generate mock users
users = MockDataGenerator.users(count=5)

# Generate mock posts for a user
posts = MockDataGenerator.posts(user_id=1, count=3)
```

## Testing

Run the test suite:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app tests/
```

Additional testing features:
- `--run-slow`: Run slow tests
- `--run-integration`: Run integration tests
- `--pdb`: Drop into debugger on failures
- `--trace`: Enter debugger at start of test

## Code Quality

The project uses several tools to maintain code quality:

### Black
- Code formatting
- Line length: 88 characters
- Configuration in `pyproject.toml`

### Flake8
- Style guide enforcement
- Docstring checking
- Complexity checking

### MyPy
- Static type checking
- Strict mode enabled
- Configuration in `pyproject.toml`

### isort
- Import sorting
- Black-compatible settings
- Configuration in `pyproject.toml`

### Pre-commit Hooks
- Automatic code formatting
- Style checking
- Type checking
- Security checks
- Configuration in `.pre-commit-config.yaml`

## Configuration

The application supports different environments:

### Development (`config/development.py`)
- Debug mode enabled
- Detailed logging
- SQL query logging
- Development tools enabled
- Mock email sending
- Auto-reload templates

### Testing (`config/testing.py`)
- Testing mode enabled
- In-memory database
- Disabled CSRF
- Suppressed emails

### Production (`config/production.py`)
- Debug disabled
- Production-level logging
- Redis caching
- Secure cookie settings
- Email sending enabled

## CLI Commands

Development commands available through `flask dev`:

### Environment Setup
```bash
flask dev setup-dev  # Set up development environment
flask dev create-mock-data  # Create mock data
```

### Information
```bash
flask dev show-routes  # List all registered routes
flask dev show-config  # Show current configuration
flask dev debug-check  # Run debug checks
```

### Maintenance
```bash
flask dev clear-logs  # Clear log files
```

## Debugging Tools

### Debug Toolbar
- Request timing
- SQL queries
- Template rendering
- Configuration
- Logging
- Profiling

Enable in development config:
```python
DEBUG_TB_ENABLED = True
DEBUG_TB_PROFILER_ENABLED = True
```

### Logging
- Structured JSON logging
- Log rotation
- Different levels per environment
- Request tracking
- Performance monitoring

### Debug Views
Available at `/debug` in development:
- `/debug/info`: Application state
- `/debug/config`: Current configuration
- `/debug/routes`: Registered routes

## Profiling Tools

### Request Profiling
- Execution time tracking
- Memory usage monitoring
- SQL query analysis
- Function call profiling

### Memory Profiling
- Memory usage tracking
- Memory leak detection
- Object allocation tracking

### Performance Profiling
- Function timing
- Call stack analysis
- Bottleneck identification

## Mock Data Generation

### Available Generators
- Users with profiles
- Posts with content
- Comments and interactions
- Relationships and connections

### Customization
```python
from utils.dev.testing import MockDataGenerator

# Custom user data
user = MockDataGenerator.user(
    username="custom_user",
    email="custom@example.com"
)

# Custom post data
post = MockDataGenerator.post(
    user_id=1,
    content="Custom content"
)
```

## Deployment

### Docker
```bash
# Build and run with Docker
docker build -t flask-app .
docker run -p 5000:5000 flask-app

# Or use docker-compose
docker-compose up
```

### Production Setup
1. Set environment variables
2. Configure Nginx (see `nginx.conf`)
3. Set up Supervisor (see `supervisor.conf`)
4. Initialize database
5. Configure Redis
6. Set up SSL certificates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks
5. Submit a pull request

### Development Workflow
1. Activate virtual environment
2. Install development dependencies
3. Set up pre-commit hooks
4. Make changes
5. Run tests and checks
6. Commit changes

## License

This project is licensed under the MIT License - see the LICENSE file for details. 