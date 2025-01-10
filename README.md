# Quiz App

A robust **Quiz Application** designed for colleges to manage quizzes for students efficiently. This app allows administrators to assign multiple quizzes, set time limits, record scores, calculate ranks, and organize students into classes. Quiz questions can be added or uploaded via a file, with random selection based on admin preferences.

---

## Features

### **Admin Panel**
- **Quiz Management**: Create, assign, and schedule quizzes for specific classes.
- **Question Management**: 
  - Add questions manually or via file upload (e.g., CSV or Excel).
  - Randomize questions for each quiz based on admin-defined parameters.
- **Scoreboard**: View and rank students by scores across quizzes.
- **Class Management**: Manage student lists, assign classes, and track performance.

### **Student Panel**
- **Quiz Attempt**: 
  - Attempt assigned quizzes within the time limit.
  - Real-time quiz timer.
- **Performance Insights**: View scores, ranks, and quiz history.

---

## Tech Stack

- **Backend**: Flask (with SQLAlchemy ORM)
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
---

### Snapshots

Here are some snapshots of the Flask Quiz App to give you a quick preview of its features and functionality.

#### **Login**
- Simple login with username and password.  
![Login](./snapshot/login)

#### **Create Quiz**
- Admin interface to set up quizzes, select classes, and define time limits.  
![Create Quiz](./snapshot/addquiz)

#### **Student Dashboard**
- View assigned quizzes, attempt quizzes, and track performance history.  
![Student Dashboard](./snapshot/dashboard)
