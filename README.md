# Blood Bank Management System — Python/Flask

## Tech Stack
- **Python** · Flask · SQLite · Jinja2 · HTML/CSS

---

## Setup & Run

### 1. Install dependencies
```bash
pip install flask
```

### 2. Run the app
```bash
python app.py
```

### 3. Open in browser
```
http://localhost:5000
```

The SQLite database (`blood_bank.db`) is created automatically with sample data on first run.

---

## Login Credentials

| Role     | Username / Email     | Password  |
|----------|---------------------|-----------|
| Admin    | admin               | admin123  |
| Hospital | city@hosp.in        | hosp123   |
| Hospital | apollo@med.in       | hosp123   |
| Hospital | sunrise@cl.in       | hosp123   |

---

## Features
- Home page with live stats and blood availability
- About & Contact pages
- **Admin portal**: full CRUD for donors, hospitals, inventory, requests
- **Hospital portal**: submit requests, view status, check availability
- Auto inventory deduction on approval
- Low stock alerts (below 20 units)

---

## Project Structure
```
blood_bank/
├── app.py                  ← Flask app + all routes
├── requirements.txt
├── blood_bank.db           ← SQLite DB (auto-created)
├── static/css/
│   └── style.css
└── templates/
    ├── base.html
    ├── index.html
    ├── login.html
    ├── about.html
    ├── contact.html
    ├── admin/
    │   ├── base.html
    │   ├── dashboard.html
    │   ├── donors.html
    │   ├── register_donor.html
    │   ├── edit_donor.html
    │   ├── hospitals.html
    │   ├── register_hospital.html
    │   ├── edit_hospital.html
    │   ├── inventory.html
    │   ├── add_inventory.html
    │   ├── edit_inventory.html
    │   └── requests.html
    └── hospital/
        ├── base.html
        ├── request.html
        ├── my_requests.html
        └── availability.html
```
