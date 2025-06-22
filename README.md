# 🧬 GenepoweRx Healthcare Dashboard

This project is a full-stack **clinical reporting dashboard** designed for GenepoweRx, a genomics-based healthtech platform. The dashboard streamlines the process of submitting, storing, viewing, and managing patient health reports, with direct integration into a **MongoDB backend** and **PDF/Excel file handling**.

---

## 🚀 Key Functionalities

- 📤 Upload PDF reports (Bloodwork, Consent, etc.) directly from the frontend
- 📥 Store structured JSON and file data in **MongoDB**
- 📊 Submit patient health reports with **AI scores** and **severity levels**
- 📧 Generate Excel files from report data and **send via email** with attachments
- 👁️ Toggle fullscreen mode and condition severity
- ✅ Manage patient availability and submission status dynamically

---

## 🗂️ Modules Overview

### 🔍 **DashboardSearch Component**
- **Batch Selection:** Dropdown to select patient batches from API.
- **Patient Search:** Real-time patient filtering with interactive selection.
- **Availability Toggle:** Enable/disable patient availability unless already submitted.
- **Color-coded Status:**
  - 🟢 Green – Report Submitted
  - 🟠 Orange – Available
  - 🔴 Red – Not Available

---

### 📋 **Report & Condition Handling**
- Display and toggle between multiple conditions per patient
- Use of color buttons to reflect:
  - 🟠 Concern
  - 💚 Selected
  - 🟢 Viewed & Reported

---

### 🖥️ **Fullscreen Mode**
- Toggle into fullscreen for an immersive view
- View AI-generated scores and mutation indicators
- Dynamically render selected condition details
- Designed with scrollable and responsive UI

---

### 📄 **PDF Viewer**
- Supports multi-page PDFs (e.g., 1 / 44 pages)
- Navigation controls (zoom in/out, reset, page nav)
- Categorized display of reports: PDF, Consent, Blood Reports
- Download & Settings menu

---

### 📬 **Patient Report Submission Flow**
- Input form to submit patient data (ID, batch, condition)
- PDF upload stored in MongoDB
- Report data exported as Excel and emailed automatically
- Email attachments auto-deleted after sending

---

## 🛠 Tech Stack

- **Frontend:** ReactJS
- **Backend:** Node.js, Express
- **Database:** MongoDB
- **Email Service:** Nodemailer / SMTP
- **File Handling:** Multer for uploads
- **PDF Tools:** PDF.js / React-PDF for rendering
