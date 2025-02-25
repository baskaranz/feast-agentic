# Agentic AI with Feast Feature Store - Frontend

This is the frontend component of the Agentic AI with Feast Feature Store demo application. It provides a React-based user interface for interacting with the AI agent and visualizing its actions and results.

## Features

- Interactive dashboard for different AI agent use cases
- Visualizations for product recommendations, fraud detection, and customer segmentation
- Real-time agent activity monitoring
- Feature store information display
- Graceful handling of API connection issues with fallback to mock data

## Setup

### Prerequisites

- Node.js 14+ and npm 6+
- Backend API running (typically on http://localhost:8000)

### Installation

1. Install dependencies:

```bash
npm install
```

2. Start the development server:

```bash
npm start
```

The frontend will be available at http://localhost:3000

## Development

This project uses:

- React for the UI framework
- Tailwind CSS for styling
- Recharts for data visualization
- Axios for API requests

## Project Structure

- `src/components/AgenticAIDashboard.jsx` - Main dashboard component
- `src/App.js` - Root App component
- `src/index.js` - Application entry point

## Available Scripts

- `npm start` - Runs the app in development mode
- `npm test` - Launches the test runner
- `npm run build` - Builds the app for production
- `npm run eject` - Ejects from Create React App (one-way operation)

## Environment Variables

Environment variables are stored in the `.env` file:

- `REACT_APP_API_URL` - URL of the backend API

## Notes for Production Use

This is a demonstration application. For production use, consider:

1. Adding proper authentication and authorization
2. Implementing more robust error handling
3. Adding comprehensive testing
4. Setting up CI/CD pipelines
5. Optimizing the build for performance