# Mercury AI Assistant - Frontend

A modern React + TypeScript + Tailwind CSS frontend for the Mercury AI Assistant platform.

## Features

- **Product Search**: Advanced search with filters, sorting, and autocomplete suggestions
- **AI Chat**: Real-time chat with Gemini 2.5 Flash AI assistant
- **Image Search**: Upload images to search for similar products or detect barcodes
- **Conversations**: Manage your chat history
- **Personalized Recommendations**: Get product suggestions based on your preferences
- **User Profile**: View and manage your preferences and activity

## Tech Stack

- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **Vite** for fast development and builds
- **Zustand** for state management
- **Axios** for API calls

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
cd app/frontend
npm install
```

### Development

```bash
npm run dev
```

The app will run on `http://localhost:3000`

### Build

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=/api
```

## Deployment

### Vercel (Recommended)

1. Push your code to GitHub
2. Import the project to Vercel
3. Add environment variables
4. Deploy

### Netlify

1. Push your code to GitHub
2. Connect repository in Netlify
3. Set build command: `npm run build`
4. Set publish directory: `dist`
5. Add environment variables
6. Deploy

## API Integration

The frontend connects to the backend at `/api`. Configure the backend URL in `vite.config.ts` or via environment variables.

## Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/          # Page components
│   ├── context/        # React context providers
│   ├── api/            # API client and service modules
│   ├── hooks/          # Custom React hooks
│   ├── utils/          # Utility functions
│   └── main.tsx        # App entry point
├── public/             # Static assets
├── index.html          # HTML template
├── tailwind.config.js  # Tailwind configuration
├── vite.config.ts      # Vite configuration
└── package.json
```
