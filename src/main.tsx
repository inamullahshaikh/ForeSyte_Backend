import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
// import StudentDashboardPage from './student-portal/dashboard.tsx'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
    {/* <StudentDashboardPage/> */}
  </StrictMode>,
)
