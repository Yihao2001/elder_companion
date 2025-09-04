# ElderComp Caregiver Interface

A web-based interface for caregivers to manage elderly profiles, view personal preferences, and access medical summaries in the ElderComp system.

## 🏗️ Architecture

The caregiver interface consists of two main components:

### Backend (FastAPI)
- **Authentication**: JWT-based authentication with hardcoded demo users
- **Database Integration**: Connects to PostgreSQL database with encrypted medical data
- **API Endpoints**: RESTful API for elderly profiles, preferences, and medical summaries
- **Security**: Role-based access control and data encryption

### Frontend (React + TypeScript)
- **Authentication**: Login form with JWT token management
- **Dashboard**: Overview statistics and quick actions
- **Elderly Management**: List and detailed views of elderly profiles
- **Responsive Design**: Mobile-friendly interface with modern styling

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL with pgvector extension (running via Docker)

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd caregiver_interface/backend
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # The .env file is already created with default values
   # Modify caregiver_interface/backend/.env if needed
   ```

4. **Start the backend server**
   ```bash
   python main.py
   # Or using uvicorn directly:
   # uvicorn main:app --reload --host 0.0.0.0 --port 8001
   ```

   The backend API will be available at: http://localhost:8001

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd caregiver_interface/frontend
   ```

2. **Install Node.js dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm start
   ```

   The frontend will be available at: http://localhost:3000

### Database Setup

Make sure the PostgreSQL database is running with sample data:

```bash
cd database
docker-compose up -d
```

## 🔐 Authentication

The system uses hardcoded demo users for authentication:

| Username     | Password      | Role                 |
| ------------ | ------------- | -------------------- |
| `caregiver1` | `password123` | Primary Caregiver    |
| `admin`      | `admin123`    | System Administrator |

## 📊 Features

### Dashboard
- Overview statistics (total elderly, preferences, medical records)
- Quick navigation to elderly profiles
- System health information

### Elderly Profiles
- List view of all elderly individuals
- Detailed profile information
- Personal preferences organized by category
- Medical summary (non-sensitive data only)

### Security Features
- JWT token-based authentication
- Automatic token refresh
- Protected routes
- Encrypted medical data (backend only shows summaries)

## 🛠️ API Endpoints

### Authentication
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user info

### Elderly Management
- `GET /elderly` - List all elderly profiles
- `GET /elderly/{id}` - Get specific elderly profile
- `GET /elderly/{id}/preferences` - Get personal preferences
- `POST /elderly/{id}/preferences` - Add new preference
- `GET /elderly/{id}/medical-summary` - Get medical summary

### Health Check
- `GET /health` - System health status

## 🎨 Frontend Components

### Core Components
- **Login**: Authentication form with demo credentials
- **Dashboard**: Main overview page with statistics
- **ElderlyList**: Grid view of all elderly profiles
- **ElderlyDetail**: Detailed view with preferences and medical summary

### Context
- **AuthContext**: Manages authentication state and JWT tokens

### Styling
- Modern CSS with gradient backgrounds
- Responsive grid layouts
- Card-based design system
- Mobile-friendly interface

## 🔧 Configuration

### Backend Configuration
Environment variables in `caregiver_interface/backend/.env`:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=eldercomp
DB_USER=postgres
DB_PASSWORD=password

# Security
SECRET_KEY=eldercomp_secret_key_change_in_production
ENCRYPTION_KEY=eldercomp_encryption_key_change_in_production
```

### Frontend Configuration
- Proxy configuration in `package.json` routes API calls to backend
- TypeScript configuration for modern JavaScript features
- React 18 with functional components and hooks

## 🧪 Testing

### Backend Testing
```bash
cd caregiver_interface/backend
# Test authentication
curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "caregiver1", "password": "password123"}'

# Test health check
curl "http://localhost:8001/health"
```

### Frontend Testing
- Open browser to http://localhost:3000
- Login with demo credentials
- Navigate through dashboard and elderly profiles

## 🔒 Security Considerations

### Production Deployment
1. **Change default passwords and keys**
   - Update `SECRET_KEY` and `ENCRYPTION_KEY`
   - Replace hardcoded users with database-backed authentication

2. **Enable HTTPS**
   - Configure SSL certificates
   - Update CORS settings

3. **Database Security**
   - Use strong database passwords
   - Enable database SSL connections
   - Implement proper backup procedures

4. **Environment Variables**
   - Use secure environment variable management
   - Never commit sensitive data to version control

## 🚨 Troubleshooting

### Common Issues

1. **Backend won't start**
   - Check if PostgreSQL is running: `docker ps`
   - Verify database connection in `.env` file
   - Check Python dependencies: `pip install -r requirements.txt`

2. **Frontend build errors**
   - Clear node_modules: `rm -rf node_modules && npm install`
   - Check Node.js version: `node --version` (should be 16+)

3. **Authentication issues**
   - Check if backend is running on port 8001
   - Verify demo credentials are correct
   - Check browser console for network errors

4. **Database connection errors**
   - Ensure Docker containers are running
   - Check database logs: `docker logs eldercomp_postgres`
   - Verify database initialization completed

### Logs and Debugging

- **Backend logs**: Check terminal where `python main.py` is running
- **Frontend logs**: Check browser developer console
- **Database logs**: `docker logs eldercomp_postgres`

## 📈 Performance

### Optimization Tips
- Backend uses connection pooling for database efficiency
- Frontend implements lazy loading for large datasets
- Medical data encryption is handled at database level
- JWT tokens have reasonable expiration times

### Scaling Considerations
- Backend can be horizontally scaled with load balancers
- Database read replicas can be added for better performance
- Frontend can be served from CDN for better global performance

## 🤝 Development

### Adding New Features

1. **New API Endpoints**
   - Add routes to `caregiver_interface/backend/main.py`
   - Update Pydantic models for request/response validation
   - Add authentication decorators for protected endpoints

2. **New Frontend Components**
   - Create components in `caregiver_interface/frontend/src/components/`
   - Add routes to `App.tsx`
   - Update navigation and styling as needed

3. **Database Changes**
   - Modify database schema in `database/init.sql`
   - Update backend models and queries
   - Test with sample data

### Code Style
- Backend: Follow PEP 8 Python style guide
- Frontend: Use TypeScript with strict mode
- Use meaningful variable names and comments
- Implement proper error handling

---

**ElderComp Caregiver Interface** - Secure, user-friendly elderly care management 👩‍⚕️💙
