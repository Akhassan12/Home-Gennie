# AR Interior Dashboard 🏠

A modern web application for interior design projects with **Google Gemini AI-powered** room analysis and AR visualization capabilities.

## ✨ Features

- **User Authentication** - Secure login/registration with email verification
- **Project Management** - Create and manage interior design projects
- **Budget Tracking** - Monitor project budgets and expenses
- **Wishlist Management** - Save and organize furniture and decor items
- **AI Room Analysis** - Upload room images for AI-powered design insights
- **Design Generation** - Get AI-generated design suggestions
- **AR Visualization** - View designs in augmented reality
- **Profile Management** - User profiles with customizable settings

## 🗄️ Database Options

This application supports both SQLite (development) and PostgreSQL (production).

### SQLite (Default - Development)
- ✅ Easy setup, no configuration needed
- ✅ Perfect for development and testing
- ❌ Not suitable for production with multiple users

### PostgreSQL (Recommended - Production)
- ✅ Production-ready with ACID compliance
- ✅ Excellent performance and scalability
- ✅ Advanced features for complex queries
- ✅ Better concurrency handling

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL (for production) or SQLite (for development)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd ar-interior-dashboard
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Setup database**

   **For SQLite (Development):**
   ```bash
   # No setup required - uses file-based database
   ```

   **For PostgreSQL (Production):**

   **Windows Installation:**
   ```bash
   # Download PostgreSQL installer from: https://www.postgresql.org/download/windows/
   # Install with default settings (port 5432)

   # After installation, create database using pgAdmin or command line:
   # Open Command Prompt as Administrator
   psql -U postgres -c "CREATE DATABASE ar_interior_db;"
   psql -U postgres -c "CREATE USER your_user WITH PASSWORD 'your_password';"
   psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE ar_interior_db TO your_user;"

   # Or use pgAdmin GUI to create database and user
   ```

   **Linux/Unix Installation:**
   ```bash
   # Install PostgreSQL
   sudo apt update && sudo apt install postgresql postgresql-contrib

   # Create database and user
   sudo -u postgres psql -c "CREATE DATABASE ar_interior_db;"
   sudo -u postgres psql -c "CREATE USER your_user WITH PASSWORD 'your_password';"
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ar_interior_db TO your_user;"
   ```

   **Update .env file**
   ```bash
   # Add to your .env file
   DATABASE_URL=postgresql://your_user:your_password@localhost:5432/ar_interior_db
   ```

   **Initialize migrations**
   ```bash
   python migrations.py db init
   python migrations.py db migrate
   python migrations.py db upgrade
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Open in browser**
   ```
   http://localhost:5000
   ```

## 🗄️ Database Migration

### From SQLite to PostgreSQL

1. **Backup your SQLite data** (if any)
   ```bash
   cp instance/ar_interior.db instance/ar_interior.db.backup
   ```

2. **Update your .env file**
   ```bash
   DATABASE_URL=postgresql://username:password@localhost:5432/ar_interior_db
   ```

3. **Install PostgreSQL** and create database (see setup instructions above)

4. **Initialize Flask-Migrate**
   ```bash
   python migrations.py db init
   ```

5. **Create migration**
   ```bash
   python migrations.py db migrate -m "Initial migration"
   ```

6. **Apply migration**
   ```bash
   python migrations.py db upgrade
   ```

### Migration Commands

```bash
# Initialize migrations (first time only)
python migrations.py db init

# Create new migration
python migrations.py db migrate -m "Description of changes"

# Apply migrations
python migrations.py db upgrade

# Rollback migrations
python migrations.py db downgrade

# Check migration status
python migrations.py db current

# Show migration history
python migrations.py db history
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | Required |
| `DATABASE_URL` | Database connection URL | `sqlite:///ar_interior.db` |
| `MAIL_SERVER` | SMTP server | `smtp.gmail.com` |
| `MAIL_PORT` | SMTP port | `587` |
| `MAIL_USERNAME` | Email username | Required for email features |
| `MAIL_PASSWORD` | Email password/app password | Required for email features |
| `GEMINI_API_KEY` | Google Gemini API key | Required for AI features |

### PostgreSQL Connection String Formats

```bash
# Basic format
postgresql://username:password@hostname:port/database_name

# Examples
postgresql://myuser:mypass@localhost:5432/ar_interior_db
postgresql://postgres:password@db.example.com:5432/myapp
```

## 🛠️ Development Tools

### Database Management

**Reset Database:**
```bash
python tools/reset_db.py
```

**Database Editor (Interactive):**
```bash
python tools/db_editor.py
```

### Testing

**Run all tests:**
```bash
python test_app.py
python test_modular.py
```

## 📁 Project Structure

```
ar-interior-dashboard/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── migrations.py         # Database migration script
├── .env.example          # Environment configuration template
├── services/             # AI service modules
│   ├── ai_image_analyzer.py
│   └── design_generator.py
├── templates/            # HTML templates
│   ├── auth.html
│   ├── dashboard.html
│   ├── design_suggestions.html
│   └── ar_view.html
├── static/               # CSS, JavaScript, and assets
│   ├── css/
│   └── js/
└── tools/                # Utility scripts
    ├── reset_db.py
    └── db_editor.py
```

## 🚀 Deployment

### Production Deployment

1. **Use PostgreSQL** (not SQLite)
2. **Set production environment variables**
3. **Configure production email service**
4. **Set up reverse proxy** (nginx recommended)
5. **Configure SSL/TLS certificates**
6. **Set up monitoring and logging**

### Recommended Production Stack

- **Database:** PostgreSQL
- **Web Server:** Gunicorn + Nginx
- **Email Service:** SendGrid or Amazon SES
- **File Storage:** AWS S3 or similar
- **Monitoring:** Sentry for error tracking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if necessary
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues:

1. Check the logs for error messages
2. Verify your environment configuration
3. Ensure all dependencies are installed
4. Check database connectivity
5. Review the troubleshooting section

For PostgreSQL-specific issues:

**Windows:**
- Verify PostgreSQL is running in Windows Services
- Use pgAdmin to check databases and users
- Test connection: Open Command Prompt and run `psql -U postgres -d postgres`

**Linux/Unix:**
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check database exists: `sudo -u postgres psql -l`
- Test connection: `psql -h localhost -U username -d database_name`
