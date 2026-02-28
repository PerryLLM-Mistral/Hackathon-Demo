import './sass/Navbar.sass'
import { Link } from 'react-router-dom'

const Navbar = () => {
    

    return (
        <div className='navbar'>
            <Link to='/' className='navbar-link'>HOME</Link>
            <Link to='/map' className='navbar-link'>MAP</Link>
        </div>
    )
}

export default Navbar
