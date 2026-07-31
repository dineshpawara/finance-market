import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import AppRoutes from './routes/AppRoutes.tsx'
import { ThemeProvider } from './context/ThemeContext.tsx'
import { PaperTradingProvider } from './context/PaperTradingContext.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider>
      <PaperTradingProvider>
        <AppRoutes />
      </PaperTradingProvider>
    </ThemeProvider>
  </StrictMode>,
)
