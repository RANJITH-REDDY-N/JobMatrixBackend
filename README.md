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
