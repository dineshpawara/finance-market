import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import AppRoutes from './routes/AppRoutes.tsx'
import { ThemeProvider } from './context/ThemeContext.tsx'
import { PaperTradingProvider } from './context/PaperTradingContext.tsx'
import { AuthProvider } from './context/AuthContext.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider>
      <AuthProvider>
        <PaperTradingProvider>
          <AppRoutes />
        </PaperTradingProvider>
      </AuthProvider>
    </ThemeProvider>
  </StrictMode>,
)
