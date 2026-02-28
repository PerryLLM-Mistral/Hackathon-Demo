import { BrowserRouter as Router, Routes, Route } from "react-router-dom"
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Map from './pages/Map'

function App() {
    return (
        <Router>
            <Navbar />

            <Routes>
                <Route path='/' element={<Home />} />
                <Route path='/map' element={<Map />} />
            </Routes>
        </Router>
    )
}

export default App
