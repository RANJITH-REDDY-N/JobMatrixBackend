# JobMatrix Backend

A robust Django-based backend service for the JobMatrix application, providing job management and user profile functionality.

## Features

- User Authentication with JWT
- Profile Management
- Job Management
- Email Integration (SendGrid)
- AWS Integration
- RESTful API Architecture
- CORS Support
- Database: MySQL

## Prerequisites

- Python 3.8+
- MySQL
- Docker (optional)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd JobMatrixBackend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with the following variables:

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings (AWS RDS)
DB_NAME=jobmatrix
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=3306

# JWT Settings
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_LIFETIME=5
JWT_REFRESH_TOKEN_LIFETIME=1

# Email Settings (SendGrid)
SENDGRID_API_KEY=your-sendgrid-api-key
EMAIL_FROM=your-verified-sender@example.com

# AWS Settings (S3 Bucket)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=your-region
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Start the development server:
```bash
python manage.py runserver
```

## Docker Setup

1. Build the Docker image:
```bash
docker build -t jobmatrix-backend .
```

2. Run with Docker Compose:
```bash
docker-compose up
```

## API Documentation

The API documentation is available at `/api/docs/` when running the server.

## Project Structure

```
JobMatrixBackend/
├── Job/                 # Job management app
├── Profile/            # User profile management app
├── JobMatrix/          # Main project settings
├── config/             # Configuration files
├── manage.py           # Django management script
├── requirements.txt    # Project dependencies
├── dockerfile         # Docker configuration
└── docker-compose.yml # Docker Compose configuration
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email support@jobmatrix.com or create an issue in the repository.

## Frontend Repository  
The client-side code logic can be found here:  
[Frontend Repo](https://github.com/RANJITH-REDDY-N/JobMatrixFrontend)

### Prerequisites
- Python 3.10+
- MySQL
- pip

### Installation

```bash


# Clone the repository
git clone https://github.com/RANJITH-REDDY-N/JobMatrixBackend
cd JobMatrixBackend

# Create virtual environment
python -m venv venv

# Activate environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

#To setup the Database
python manage.py migrate

#To Run The Application
python manage.py runserver
```

## .env (should look some thing like this)

```bash

SECRET_KEY= ******
DEBUG=True

# Database Configuration
DB_ENGINE=django.db.backends.mysql
DB_NAME=******
DB_USER=******
DB_PASSWORD=******
DB_HOST=******
DB_PORT=3306

# JWT Configuration
JWT_SECRET=******
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DAYS=1

# Admin secret
ADMIN_SECRET_KEY=******

#Use SENDGRID Credentials to get verification code.
SENDGRID_API_KEY=******
DEFAULT_FROM_EMAIL=example@gmail.com

```

# Proxy Configuration Example

This repository includes a basic example proxy configuration file: `.env.proxy`.

## Purpose

This file provides a template for setting environment variables commonly used to configure applications to use an HTTP or HTTPS proxy. It's useful for development or testing environments where outgoing network traffic needs to go through a proxy.

## Usage

1.  Rename `.env.proxy` to `.env` or copy its contents to your existing `.env` file.
2.  Uncomment and update the relevant `HTTP_PROXY`, `HTTPS_PROXY`, and `NO_PROXY` variables with your proxy server details.
3.  Ensure your application is configured to read environment variables (e.g., using a library like `python-dotenv`).

**Note:** Some tools and operating systems might use lowercase `http_proxy`, `https_proxy`, and `no_proxy`. It's often best to define both uppercase and lowercase versions for compatibility.

## Example `.env.proxy` content:

```dotenv
# Example proxy configuration
# Uncomment and replace with your proxy details

# HTTP proxy for non-HTTPS requests
# HTTP_PROXY="http://your_proxy_server:your_proxy_port"
# http_proxy="http://your_proxy_server:your_proxy_port"

# HTTPS proxy for HTTPS requests
# HTTPS_PROXY="http://your_proxy_server:your_proxy_port"
# https_proxy="http://your_proxy_server:your_proxy_port"

# List of hosts that should not be proxied (comma-separated)
# NO_PROXY="localhost,127.0.0.1,.example.com"
# no_proxy="localhost,127.0.0.1,.example.com"
```

Remember to replace `"http://your_proxy_server:your_proxy_port"` and `"localhost,127.0.0.1,.example.com"` with your actual proxy configuration.

This is a basic example. Depending on your specific proxy setup and application requirements, you might need additional configuration.
