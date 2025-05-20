# JobMatrix Backend (Django)

## 🚀 Getting Started

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
