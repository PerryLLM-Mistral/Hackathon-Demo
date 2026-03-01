import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.sass'
import App from './App.jsx'

// TODO: StrictMode is removed so the websocket works correctly in dev, need to added it back for production
createRoot(document.getElementById('root')).render(
//    <StrictMode>
        <App />
//    </StrictMode>,
)
