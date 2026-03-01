import './sass/Navbar.sass'
import { Link } from 'react-router-dom'
import logo from '../assets/logo.svg'

const Navbar = () => {
    

    return (
        <div className='navbar'>
            <img src={logo} alt="Logo" width="90" />
            <Link to='/' className='navbar-link'>HOME</Link>
            <Link to='/map' className='navbar-link'>MAP</Link>
        </div>
    )
}

export default Navbar
