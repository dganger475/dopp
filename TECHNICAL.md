# Doppleganger Social Network - Technical Documentation

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Backend Architecture](#backend-architecture)
3. [Frontend Architecture](#frontend-architecture)
4. [Database Design](#database-design)
5. [API Endpoints](#api-endpoints)
6. [Deployment Architecture](#deployment-architecture)
7. [Security Measures](#security-measures)
8. [Performance Optimizations](#performance-optimizations)

## Architecture Overview

The Doppleganger Social Network is a full-stack web application built with a Flask backend and React frontend. The application uses a microservices architecture with the following key components:

- Flask Backend (Python)
- React Frontend (JavaScript/TypeScript)
- PostgreSQL Database
- Redis for Caching
- Backblaze B2 for File Storage
- FAISS for Vector Search
- Docker for Containerization

## Backend Architecture

### Core Components

#### Flask Application Factory
The application uses Flask's application factory pattern (`app.py`) for flexible initialization across different environments. Key features include:

- Environment-based configuration
- Blueprint-based routing
- Extension initialization
- Session management
- CORS configuration
- Template helpers

#### Blueprints Structure
The application is organized into the following blueprints:

1. **Main Routes** (`routes/main.py`)
   - Homepage
   - Core application views

2. **Authentication** (`routes/auth.py`)
   - User registration
   - Login/logout
   - Password management
   - Session handling

3. **Search** (`routes/search.py`)
   - Face search functionality
   - Vector similarity search
   - Search result processing

4. **Profile Management** (`routes/profile/`)
   - Profile viewing
   - Profile editing
   - Profile updates
   - Image management

5. **Face Processing** (`routes/face.py`)
   - Face detection
   - Face recognition
   - Face comparison
   - Face upload handling

6. **Social Features** (`routes/social.py`)
   - User interactions
   - Notifications
   - Social connections

7. **API Endpoints** (`routes/api/`)
   - RESTful API endpoints
   - Mobile API support
   - CORS proxy

8. **Admin Panel** (`routes/admin.py`)
   - Administrative functions
   - System monitoring
   - User management

### Key Extensions and Middleware

1. **Security**
   - Flask-Talisman for security headers
   - Flask-Limiter for rate limiting
   - Flask-Session for session management
   - CSRF protection
   - CORS middleware

2. **Database**
   - SQLAlchemy ORM
   - Flask-Migrate for database migrations
   - Connection pooling
   - Query optimization

3. **Caching**
   - Redis-based caching
   - Flask-Caching integration
   - Cache invalidation strategies

4. **File Storage**
   - Backblaze B2 integration
   - File upload handling
   - Image processing

## Frontend Architecture

### React Application Structure

The frontend is built with React and uses Vite as the build tool. Key components include:

1. **Component Organization**
   - Atomic design pattern
   - Reusable components
   - Page components
   - Layout components

2. **State Management**
   - React Context
   - Custom hooks
   - State persistence

3. **Routing**
   - React Router
   - Protected routes
   - Route guards

4. **Styling**
   - CSS Modules
   - Responsive design
   - Theme support

### Key Features

1. **User Interface**
   - Responsive design
   - Progressive loading
   - Error boundaries
   - Loading states

2. **Image Processing**
   - Client-side image optimization
   - Upload handling
   - Preview generation

3. **Search Interface**
   - Real-time search
   - Filter components
   - Result display

## Database Design

### Core Tables

1. **Users**
   - Authentication data
   - Profile information
   - Preferences

2. **Faces**
   - Face encodings
   - Image metadata
   - Search vectors

3. **Social**
   - Connections
   - Interactions
   - Notifications

### Indexes and Optimization

1. **Search Optimization**
   - FAISS vector index
   - B-tree indexes
   - Full-text search

2. **Query Optimization**
   - Connection pooling
   - Query caching
   - Index usage

## API Endpoints

### RESTful API Structure

1. **Authentication**
   - POST /api/auth/login
   - POST /api/auth/register
   - POST /api/auth/logout

2. **User Management**
   - GET /api/users/profile
   - PUT /api/users/profile
   - GET /api/users/search

3. **Face Operations**
   - POST /api/faces/upload
   - GET /api/faces/search
   - GET /api/faces/compare

4. **Social Features**
   - POST /api/social/connect
   - GET /api/social/feed
   - POST /api/social/interact

## Deployment Architecture

### Containerization

1. **Docker Configuration**
   - Multi-stage builds
   - Optimized layers
   - Environment variables

2. **Gunicorn Configuration**
   - Worker configuration
   - Thread management
   - Logging setup

### Infrastructure

1. **Web Server**
   - Gunicorn
   - Nginx (if used)
   - SSL/TLS configuration

2. **Database**
   - PostgreSQL
   - Connection pooling
   - Backup strategy

3. **File Storage**
   - Backblaze B2
   - CDN integration
   - Cache headers

## Security Measures

1. **Authentication**
   - JWT tokens
   - Session management
   - Password hashing

2. **Authorization**
   - Role-based access
   - Permission checks
   - API key management

3. **Data Protection**
   - Input validation
   - XSS prevention
   - CSRF protection

4. **Rate Limiting**
   - IP-based limits
   - User-based limits
   - API rate limiting

## Performance Optimizations

1. **Backend**
   - Query optimization
   - Caching strategies
   - Connection pooling

2. **Frontend**
   - Code splitting
   - Lazy loading
   - Asset optimization

3. **Database**
   - Index optimization
   - Query caching
   - Connection management

4. **File Storage**
   - CDN integration
   - Image optimization
   - Cache headers

## Development Workflow

1. **Local Development**
   - Docker Compose setup
   - Hot reloading
   - Debug configuration

2. **Testing**
   - Unit tests
   - Integration tests
   - End-to-end tests

3. **CI/CD**
   - GitHub Actions
   - Automated testing
   - Deployment pipeline

## Monitoring and Logging

1. **Application Monitoring**
   - Error tracking
   - Performance metrics
   - User analytics

2. **Logging**
   - Structured logging
   - Log rotation
   - Log aggregation

## Backup and Recovery

1. **Database Backups**
   - Automated backups
   - Point-in-time recovery
   - Backup verification

2. **File Storage**
   - Redundant storage
   - Version control
   - Recovery procedures 