# Grievance Resolver Frontend

React-based frontend for the Agentic Public Grievance Resolver system.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create `.env` file:
```bash
cp .env.example .env
```

3. Update `.env` with your API URL:
```
VITE_API_URL=http://localhost:8000
```

4. Start development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Features

- **File Complaint**: Submit complaints with location picker
- **Check Status**: Track complaint status using Complaint ID
- **Dashboard**: View system-wide metrics (admin)
- **Notifications**: Email notifications for status updates
- **Maps Integration**: Interactive map for location selection

## Tech Stack

- React 18
- React Router
- Leaflet Maps
- Axios
- Lucide Icons
- Vite

