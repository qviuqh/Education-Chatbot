import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

console.log('Main.jsx loaded');
console.log('Root element:', document.getElementById('root'));

try {
  createRoot(document.getElementById('root')).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
  console.log('App rendered successfully');
} catch (error) {
  console.error('Error rendering app:', error);
  document.body.innerHTML = `<div style="color: red; padding: 20px; font-family: monospace;">
    <h1>Error Loading App</h1>
    <pre>${error.message}\n${error.stack}</pre>
  </div>`;
}
