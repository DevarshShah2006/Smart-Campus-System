# Smart Campus System

QR-Based Attendance + Academics + Campus Services + Analytics

## Tech Stack
- Python + Streamlit
- SQLite
- NumPy, Matplotlib, Pandas
- JavaScript only for browser geolocation

## Setup (Windows PowerShell)
Run these commands from the project root.

1. Check Python version
```powershell
python --version
```

2. Create and activate a virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies
```powershell
pip install -r requirements.txt
```

4. Run the app
```powershell
streamlit run app.py
```

## Default Credentials
- Admin: `admin` / `admin123`
- Teacher: `teacher` / `admin123`

## Local Network Demo
To open on mobile over the same Wi-Fi/hotspot, run:
```powershell
streamlit run app.py --server.address 0.0.0.0
```
Then open `http://<your-pc-ip>:8501` on the mobile device.

## Features Implemented
- QR-based attendance with GPS verification + time window control
- Role-based dashboards (Student / Teacher / Admin)
- Notices, resources, schedule, feedback
- Campus issues, lost & found, events + registrations
- Attendance and campus analytics (NumPy + Matplotlib)
- Search & filter across modules
- CSV exports
- System settings panel

## Database
The SQLite database is stored at:
`data/smart_campus.db`

## Notes
- Privacy-friendly: no fingerprinting, OTP, or biometrics.
- JavaScript is used only for geolocation.
- UI is Streamlit-only (no custom HTML/CSS for UI).