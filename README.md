# ERPNext Mozambique (MZ) Compliance

[![CI](https://github.com/bboa3/erpnext_mz/actions/workflows/ci.yml/badge.svg)](https://github.com/bboa3/erpnext_mz/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive ERPNext customization application designed specifically for Mozambique business compliance requirements. This app provides Mozambique-specific features, tax compliance, professional print formats, and localized business processes.

## 🌟 Features

- **Mozambique Tax Compliance**: NUIT support, local tax calculations
- **Professional Print Formats**: 14+ Mozambique-specific document templates with QR codes
- **Portuguese UOM System**: Localized units of measurement
- **Company Setup Wizard**: Streamlined Mozambique business configuration
- **Document Validation**: QR code integration for document authenticity
- **Bilingual Support**: Portuguese (MZ) and English interfaces

## 🚀 Installation

### Option 1: Standard Bench Installation (Recommended for Development)

#### Prerequisites
- [Frappe Bench](https://github.com/frappe/bench) installed and configured
- Python 3.10+ and Node.js 18+
- MariaDB/MySQL database
- Redis server

#### Installation Steps
```bash
# Navigate to your bench directory
cd $PATH_TO_YOUR_BENCH

# Get the app from GitHub
bench get-app git@github.com:bboa3/erpnext_mz.git

# Install the app on your site
bench --site your-site.local install-app erpnext_mz

# Build assets
bench build

# Migrate database
bench --site your-site.local migrate
```

### Option 2: Docker Installation (Recommended for Production)

#### Prerequisites
- Docker and Docker Compose installed
- Git for cloning the repository

#### Quick Start with Docker
```bash
# Clone the repository
git clone https://github.com/bboa3/erpnext_mz.git
cd erpnext_mz

# Create environment file
cp .env.example .env
# Edit .env with your configuration

# Start the application
docker-compose up -d

# Access the application
# Open http://localhost:8000 in your browser
```

#### Docker Compose Configuration
```yaml
# docker-compose.yml
version: '3.8'

services:
  erpnext-mz:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FRAPPE_SITE_NAME=erp.local
      - FRAPPE_ADMIN_PASSWORD=admin123
      - FRAPPE_DB_HOST=db
      - FRAPPE_DB_NAME=frappe
      - FRAPPE_DB_USER=frappe
      - FRAPPE_DB_PASSWORD=frappe123
    depends_on:
      - db
      - redis
    volumes:
      - ./sites:/home/frappe/frappe-bench/sites
      - ./logs:/home/frappe/frappe-bench/logs

  db:
    image: mariadb:10.6
    environment:
      - MYSQL_ROOT_PASSWORD=root123
      - MYSQL_DATABASE=frappe
      - MYSQL_USER=frappe
      - MYSQL_PASSWORD=frappe123
    volumes:
      - db_data:/var/lib/mysql
    ports:
      - "3306:3306"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  db_data:
  redis_data:
```

#### Dockerfile
```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    mariadb-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Install Frappe Bench
RUN pip install frappe-bench

# Create frappe user
RUN useradd -m -s /bin/bash frappe

# Switch to frappe user
USER frappe
WORKDIR /home/frappe

# Initialize Frappe Bench
RUN bench init erpnext-mz --frappe-branch version-15
WORKDIR /home/frappe/erpnext-mz

# Get ERPNext MZ app
RUN bench get-app git@github.com:bboa3/erpnext_mz.git

# Create site
RUN bench new-site erp.local --mariadb-root-password root123 --admin-password admin123

# Install ERPNext MZ
RUN bench --site erp.local install-app erpnext_mz

# Build assets
RUN bench build

# Expose port
EXPOSE 8000

# Start command
CMD ["bench", "--site", "erp.local", "start"]
```

### Option 3: Manual Installation

#### Prerequisites
- Python 3.10+ and Node.js 18+
- MariaDB/MySQL database
- Redis server
- Git

#### Installation Steps
```bash
# Clone the repository
git clone https://github.com/bboa3/erpnext_mz.git
cd erpnext_mz

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
npm install

# Configure database connection
# Edit config/database.json with your database settings

# Run migrations
python manage.py migrate

# Start the application
python manage.py runserver
```

## ⚙️ Configuration

### Environment Variables
```bash
# Database Configuration
FRAPPE_DB_HOST=localhost
FRAPPE_DB_NAME=frappe
FRAPPE_DB_USER=frappe
FRAPPE_DB_PASSWORD=your_password

# Redis Configuration
FRAPPE_REDIS_HOST=localhost
FRAPPE_REDIS_PORT=6379

# Site Configuration
FRAPPE_SITE_NAME=erp.local
FRAPPE_ADMIN_PASSWORD=admin123

# Email Configuration
FRAPPE_MAIL_SERVER=smtp.gmail.com
FRAPPE_MAIL_PORT=587
FRAPPE_MAIL_LOGIN=your_email@gmail.com
FRAPPE_MAIL_PASSWORD=your_password
```

### Site Configuration
After installation, configure your site:

1. **Access the Setup Wizard**: Navigate to ERPNext MZ module
2. **Company Information**: Enter Mozambique business details
3. **Tax Configuration**: Set up NUIT and tax accounts
4. **Print Formats**: Configure Mozambique-specific document templates
5. **UOM System**: Set up Portuguese units of measurement

## 🔧 Development

### Prerequisites
- [Frappe Bench](https://github.com/frappe/bench) development environment
- Python 3.10+ and Node.js 18+
- Git

### Development Setup
```bash
# Fork and clone the repository
git clone https://github.com/your-username/erpnext_mz.git
cd erpnext_mz

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
bench --site your-site.local run-tests --app erpnext_mz

# Start development server
bench start
```

### Code Quality Tools

This app uses `pre-commit` for code formatting and linting:

```bash
cd apps/erpnext_mz
pre-commit install
```

Pre-commit is configured to use:
- **ruff**: Python linting and formatting
- **eslint**: JavaScript/TypeScript linting
- **prettier**: Code formatting
- **pyupgrade**: Python code modernization

### Testing
```bash
# Run all tests
bench --site your-site.local run-tests --app erpnext_mz

# Run specific test file
bench --site your-site.local run-tests --app erpnext_mz --module erpnext_mz.tests.test_qr_code

# Run with coverage
bench --site your-site.local run-tests --app erpnext_mz --coverage
```

## 📚 Documentation

- [User Guide](docs/user-guide.md)
- [Developer Guide](docs/developer-guide.md)
- [API Reference](docs/api-reference.md)
- [Roadmap](erpnext_mz/roadmap.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure code quality
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Standards
- Follow PEP 8 for Python code
- Use ESLint and Prettier for JavaScript/TypeScript
- Write comprehensive tests for new features
- Update documentation for API changes

## 🚀 Deployment

### Production Considerations
- Use HTTPS in production
- Configure proper database backups
- Set up monitoring and logging
- Use a reverse proxy (nginx/Apache)
- Configure proper firewall rules

### Docker Production Deployment
```bash
# Build production image
docker build -t erpnext-mz:latest .

# Run with production settings
docker run -d \
  --name erpnext-mz-prod \
  -p 80:8000 \
  -e FRAPPE_ENV=production \
  -e FRAPPE_SITE_NAME=your-domain.com \
  erpnext-mz:latest
```

### Bench Production Deployment
```bash
# Setup production site
bench --site your-domain.com new-site --mariadb-root-password your_password

# Install app
bench --site your-domain.com install-app erpnext_mz

# Setup production
bench --site your-domain.com setup production

# Start production server
bench --site your-domain.com start
```

## 📊 Monitoring and Logs

### Log Locations
- **Application Logs**: `logs/frappe.log`
- **Error Logs**: `logs/error.log`
- **Database Logs**: `logs/database.log`
- **Worker Logs**: `logs/worker.log`

### Health Checks
```bash
# Check app status
bench --site your-site.local show-config

# Check database connection
bench --site your-site.local console --run "print(frappe.db.sql('SELECT 1'))"

# Check Redis connection
bench --site your-site.local console --run "print(frappe.cache().ping())"
```

## 🔒 Security

- All API endpoints are properly secured
- QR code validation uses HMAC hashing
- Database connections use parameterized queries
- File uploads are validated and sanitized
- Session management follows security best practices

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Frappe Framework](https://frappeframework.com/) for the excellent foundation
- [ERPNext](https://erpnext.com/) for the comprehensive ERP solution
- The open-source community for contributions and feedback

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/bboa3/erpnext_mz/issues)
- **Discussions**: [GitHub Discussions](https://github.com/bboa3/erpnext_mz/discussions)
- **Documentation**: [Wiki](https://github.com/bboa3/erpnext_mz/wiki)

---

**Deus é o Amor** - God is Love
