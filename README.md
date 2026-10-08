# 🎓 Attendance Management API

A simple and powerful **Attendance Management REST API** built using **Python, Flask, and SQLite**.

This project provides APIs to manage students, classes, attendance records, attendance reports, low-attendance students, and CSV exports.

---

## 🚀 Features

- 👨‍🎓 Add, view, update, and delete students
- 🏫 Create and manage classes
- 📝 Mark student attendance
- ⚡ Bulk attendance marking
- ⏰ Automatic **Late** status based on class timing
- 📊 Generate class-wise attendance reports
- 👤 Generate student-wise attendance reports
- ⚠️ Find students with attendance below a given percentage
- 📥 Export attendance records to CSV
- 🔐 Optional API-key authentication
- 🗄️ SQLite database
- ❤️ Health-check endpoint
- 🔄 RESTful API structure

---

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | REST API framework |
| SQLite | Database |
| JSON | API data format |
| CSV | Attendance export |
| REST API | Client-server communication |

---

## 📁 Project Structure

```text
python-project-time-pass/
│
├── project.py
├── attendance.db
└── README.md
```

> `attendance.db` is automatically created when the application initializes the database.

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/siddharthgajbhare/python-project-time-pass.git
```

### 2. Open the project folder

```bash
cd python-project-time-pass
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the virtual environment

**Windows:**

```bash
venv\Scripts\activate
```

**Linux / macOS:**

```bash
source venv/bin/activate
```

### 5. Install Flask

```bash
pip install flask
```

---

## ▶️ Run the Application

```bash
python project.py
```

The API will run at:

```text
http://127.0.0.1:5000
```

For debug mode on Windows:

```bash
set FLASK_DEBUG=1
python project.py
```

---

# 📡 API Endpoints

## 👨‍🎓 Student APIs

### Add Student

```http
POST /students
```

Example JSON:

```json
{
  "student_id": "S001",
  "name": "Siddharth Gajbhare",
  "email": "siddharth@example.com"
}
```

### Get All Students

```http
GET /students
```

### Get Student

```http
GET /students/<student_id>
```

### Update Student

```http
PUT /students/<student_id>
```

### Delete Student

```http
DELETE /students/<student_id>
```

---

# 🏫 Class APIs

### Add Class

```http
POST /classes
```

Example:

```json
{
  "class_id": "CS101",
  "name": "Computer Engineering",
  "teacher": "Professor",
  "late_after": "09:15"
}
```

### Get All Classes

```http
GET /classes
```

### Delete Class

```http
DELETE /classes/<class_id>
```

---

# 📝 Attendance APIs

### Mark Attendance

```http
POST /mark_attendance
```

Example:

```json
{
  "student_id": "S001",
  "class_id": "CS101",
  "status": "present"
}
```

Supported statuses:

```text
present
late
absent
excused
```

If a status is not provided, the API can automatically determine whether the student is **late** based on the class cutoff time.

---

## 📋 Bulk Attendance

```http
POST /bulk_attendance
```

Example:

```json
{
  "class_id": "CS101",
  "date": "2026-10-08",
  "records": [
    {
      "student_id": "S001",
      "status": "present"
    },
    {
      "student_id": "S002",
      "status": "late"
    },
    {
      "student_id": "S003",
      "status": "absent"
    }
  ]
}
```

---

## 🔍 View Attendance

```http
GET /attendance/<class_id>
```

Optional filters:

```text
?date=2026-10-08
?from=2026-10-01&to=2026-10-08
?student_id=S001
?status=present
```

Pagination is also supported:

```text
?page=1&per_page=100
```

---

# 📊 Reports

### Class Attendance Report

```http
GET /attendance_report?class_id=CS101
```

The report includes:

- Present
- Late
- Absent
- Excused
- Total sessions
- Attendance percentage

Late attendance is counted as attendance, while excused days are excluded from the denominator.

---

### Student Attendance Report

```http
GET /student_report/S001
```

Returns attendance information for the student's classes.

---

# ⚠️ Low Attendance

Find students below a specific attendance percentage.

```http
GET /low_attendance?class_id=CS101&threshold=75
```

Example:

```text
75%
```

is used as the default threshold if no threshold is specified.

---

# 📥 Export Attendance to CSV

```http
GET /export/CS101
```

The API generates a CSV file containing:

```text
id
student_id
class_id
date
timestamp
status
note
```



---

# ❤️ Health Check

Check whether the API is running:

```http
GET /health
```

Example response:

```json
{
  "status": "ok",
  "time": "2026-10-08T10:30:00"
}
```

---

# 🔐 API Key Authentication

API-key authentication is optional.

Set the environment variable:

### Windows CMD

```bash
set ATTENDANCE_API_KEY=mysecretkey
```

### PowerShell

```powershell
$env:ATTENDANCE_API_KEY="mysecretkey"
```

### Linux / macOS

```bash
export ATTENDANCE_API_KEY=mysecretkey
```

Then include the API key in protected requests:

```http
X-API-Key: mysecretkey
```

When no API key is configured, authentication is disabled.

---

# 🗄️ Database

The application uses **SQLite**.

The database contains three main tables:

### Students

```text
id
name
email
```

### Classes

```text
id
name
teacher
late_after
```

### Attendance

```text
id
student_id
class_id
date
timestamp
status
note
```

The attendance table also prevents duplicate attendance for the same student, class, and date.

---

# 🧪 Testing with Postman

You can test the API using **Postman**.

Example:

```text
POST http://127.0.0.1:5000/students
```

Headers:

```text
Content-Type: application/json
```

Body:

```json
{
  "student_id": "S001",
  "name": "Siddharth",
  "email": "siddharth@example.com"
}
```

---

# 📌 Example Workflow

```text
1. Create a class
       ↓
2. Add students
       ↓
3. Mark attendance
       ↓
4. View attendance
       ↓
5. Generate reports
       ↓
6. Check low attendance
       ↓
7. Export CSV
```

---

# 🔮 Future Improvements

- 🌐 Web-based frontend
- 👨‍🏫 Teacher dashboard
- 👨‍🎓 Student login
- 🔑 JWT authentication
- 📊 Graphical attendance dashboard
- 📧 Email notifications
- 📱 Mobile application
- ☁️ Cloud database support
- 📈 Advanced attendance analytics

---

# 👨‍💻 Author

**Siddharth Gajbhare**

GitHub:  
https://github.com/siddharthgajbhare

---

## ⭐ Support

If you found this project useful, consider giving the repository a ⭐ on GitHub.

---

## 📄 License

This project is created for **educational and learning purposes**.
