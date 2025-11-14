# EUCLOUD Frontend

React-based web interface for EUCLOUD.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Run development server:
```bash
npm run dev
```

3. Build for production:
```bash
npm run build
```

## Project Structure

```
frontend/
├── src/
│   ├── components/         # React components
│   │   ├── Header.jsx
│   │   ├── Sidebar.jsx
│   │   ├── FileBrowser.jsx
│   │   ├── UploadModal.jsx
│   │   ├── FilePreviewModal.jsx
│   │   └── ShareModal.jsx
│   ├── pages/              # Page components
│   │   ├── Login.jsx
│   │   ├── Register.jsx
│   │   └── Dashboard.jsx
│   ├── context/            # React contexts
│   │   └── AuthContext.jsx
│   ├── services/           # API services
│   │   ├── api.js
│   │   └── index.js
│   ├── App.jsx             # Root component
│   └── main.jsx            # Entry point
├── index.html
├── vite.config.js
└── package.json
```

## Features

- File upload with drag & drop
- Grid/List view toggle
- Dark mode
- File preview (images, PDFs, videos, audio)
- Share management
- Folder navigation
- Real-time search
- Context menus
- Responsive design
