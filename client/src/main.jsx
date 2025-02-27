import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import {GoogleOAuthProvider} from '@react-oauth/google'
const Client_Id=import.meta.env.VITE_CLIENT_ID
createRoot(document.getElementById('root')).render(<GoogleOAuthProvider clientId={Client_Id} ><App /></GoogleOAuthProvider>
    
)