import './sass/Navbar.sass'
import { Link } from 'react-router-dom'

const Navbar = () => {
    

    return (
        <div className='navbar'>
            <Link to='/' className='navbar-link'>Home</Link>
            <Link to='/map' className='navbar-link'>Map</Link>
        </div>
    )
}

export default Navbar
