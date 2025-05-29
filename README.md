# JobMatrix Backend  

**A robust Django-based backend service for the JobMatrix application**  

![Built with Django](https://img.shields.io/badge/Django-092E20?logo=django&logoColor=white) ![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white) ![MySQL](https://img.shields.io/badge/MySQL-4479A1?logo=mysql&logoColor=white)  

[![Frontend Repo](https://img.shields.io/badge/Frontend_Repo-181717?style=flat&logo=github&logoColor=white)](https://github.com/RANJITH-REDDY-N/JobMatrixFrontend) [![Live Demo](https://img.shields.io/badge/Live_Demo-FF5722?style=flat&logo=internet-explorer&logoColor=white)](https://jobmatrixapp.netlify.app/)  

---

## 📌 Table of Contents  
- [Features](#features)  
- [Prerequisites](#prerequisites)  
- [Installation](#installation)  
- [Docker Setup](#docker-setup)  
- [API Documentation](#api-documentation)  
- [Project Structure](#project-structure)  
- [Contributing](#contributing)   
- [Support](#support)  

---

## 🚀 Features  
- **User Authentication** with JWT  
- **Profile Management**  (AWS S3)
- **Job Management**  
- **Email Integration** (SendGrid)  
- **AWS Integration**  
- **RESTful API Architecture**  
- **CORS Support**  
- **Database**: MySQL  (AWS RDS)

---

## 🛠 Prerequisites  
- Python 3.10+  
- MySQL  
- Docker (optional)  

---

## 💻 Installation  

1. **Clone the repository**:  
   ```bash  
   git clone https://github.com/RANJITH-REDDY-N/JobMatrixBackend  
   cd JobMatrixBackend  
   ```  

2. **Set up virtual environment**:  
   ```bash  
   python -m venv venv  
   # Windows:  
   venv\Scripts\activate  
   # macOS/Linux:  
   source venv/bin/activate  
   ```  

3. **Install dependencies**:  
   ```bash  
   pip install -r requirements.txt  
   ```  

4. **Configure environment variables**:  
   Create `.env` file with:  
   ```env  
   DEBUG=True  
   DB_NAME=your_db_name  
   DB_USER=your_db_user  
   DB_PASSWORD=your_db_password  
   JWT_SECRET_KEY=your-jwt-secret  
   SENDGRID_API_KEY=your-sendgrid-key  
   ```  

5. **Run migrations**:  
   ```bash  
   python manage.py migrate  
   ```  

6. **Start server**:  
   ```bash  
   python manage.py runserver  
   ```  

---

## 🐳 Docker Setup  
1. Build the image:  
   ```bash  
   docker build -t jobmatrix-backend .  
   ```  

2. Run with Docker Compose:  
   ```bash  
   docker-compose up  
   ```  

---

## 📚 API Documentation  
Access API docs at `/api/docs/` when server is running.  

---

## 🏗 Project Structure  
```  
JobMatrixBackend/  
├── Job/                 # Job management  
├── Profile/             # User profiles  
├── JobMatrix/           # Main settings  
├── config/              # Config files  
├── manage.py            # Django CLI  
└── requirements.txt     # Dependencies  
```  

---

## 🤝 Contributing  
1. Fork the repo  
2. Create your branch (`git checkout -b feature/AmazingFeature`)  
3. Commit changes (`git commit -m 'Add feature'`)  
4. Push (`git push origin feature`)  
5. Open a PR  

---

## ❓ Support  
Create an issue in the repository  

---
