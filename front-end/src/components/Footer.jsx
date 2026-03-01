// Footer.jsx sin react-icons
import React from "react";
import "./sass/Footer.sass";

const Footer = () => {
  return (
    <footer className="footer">
      <div className="footer__content">
        <div className="footer__project">PerryLLM</div>
        <div className="footer__team">Done by: Alina Rojas Reynoso, Laura Llorente Martínez, Antonio Pérez Márquez y Laia Delgado González</div>
        <div className="footer__repo">
          <a
            href="https://github.com/PerryLLM-Mistral/Hackathon-Demo"
            target="_blank"
            rel="noopener noreferrer"
            className="footer__link"
          >
            {/* SVG de GitHub */}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.387.6.112.82-.26.82-.577 0-.285-.01-1.04-.015-2.04-3.338.726-4.042-1.61-4.042-1.61-.546-1.387-1.333-1.756-1.333-1.756-1.09-.745.083-.73.083-.73 1.205.084 1.84 1.24 1.84 1.24 1.07 1.835 2.807 1.305 3.492.998.108-.775.418-1.305.762-1.605-2.665-.305-5.467-1.333-5.467-5.93 0-1.31.468-2.38 1.235-3.22-.123-.303-.535-1.527.117-3.176 0 0 1.008-.322 3.3 1.23a11.52 11.52 0 013.003-.404c1.018.005 2.045.138 3.003.404 2.29-1.552 3.297-1.23 3.297-1.23.653 1.65.242 2.873.12 3.176.77.84 1.233 1.91 1.233 3.22 0 4.61-2.807 5.623-5.48 5.92.43.37.823 1.096.823 2.21 0 1.596-.014 2.884-.014 3.273 0 .32.216.694.825.576C20.565 21.796 24 17.296 24 12c0-6.63-5.37-12-12-12z" />
            </svg>
            GitHub
          </a>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
