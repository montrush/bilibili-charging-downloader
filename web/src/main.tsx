import React from 'react'
import ReactDOM from 'react-dom/client'
import { SkinProvider } from './theme/ThemeContext'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <SkinProvider>
      <App />
    </SkinProvider>
  </React.StrictMode>
)
