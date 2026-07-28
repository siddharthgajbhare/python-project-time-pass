"# python-project-time-pass" 
# 🎓 Student Attendance Management API

## 📌 Description

The **Student Attendance Management API** is a REST API developed using **Python and Flask**.

It allows users to mark student attendance, retrieve attendance records for a particular class, and generate attendance reports. The project demonstrates REST API development, HTTP methods, JSON handling, and basic data management using Flask.

## 🚀 Features

- ✅ Mark student attendance
- 🕒 Automatically record attendance date and time
- 🏫 Manage attendance using Class ID
- 👨‍🎓 Store attendance using Student ID
- 📋 View attendance records for a class
- 📊 Generate student-wise attendance reports
- ⚠️ Handle invalid requests and missing Class IDs
- 🔄 JSON-based API communication

## 🛠️ Technologies Used

- **Python**
- **Flask**
- **REST API**
- **JSON**
- **Python Datetime Module**

## 🔗 API Endpoints

### 1. Mark Attendance

**Method:** `POST`

**Endpoint:**
`/mark_attendance`

Example Request:

{
  "student_id": "101",
  "class_id": "CSE01"
}

### 2. Get Attendance

**Method:** `GET`

**Endpoint:**
`/attendance/<class_id>`

Example:

`/attendance/CSE01`

### 3. Generate Attendance Report

**Method:** `GET`

**Endpoint:**
`/attendance_report?class_id=CSE01`

The API returns the total number of attendance records for each student.

## ▶️ How to Run

1. Install Python.

2. Install Flask:

   pip install flask

3. Run the application:

   python app.py

4. The Flask development server will start locally.

## 📂 Project Structure

attendance-management/
│
├── app.py
├── README.md
└── requirements.txt

## ⚠️ Current Limitation

The project currently uses **in-memory storage**, so attendance records are deleted when the application restarts.

A database such as **MySQL, PostgreSQL, or MongoDB** can be integrated in future versions.

## 🔮 Future Improvements

- User/Admin authentication
- MySQL database integration
- Student registration
- Class management
- Attendance percentage calculation
- Date-wise attendance reports
- Web-based dashboard
- Export reports to CSV/PDF

## 👤 Author

**Siddharth Gajbhare**

## ⭐ Note

This project was developed for learning REST API development using Python and Flask.
