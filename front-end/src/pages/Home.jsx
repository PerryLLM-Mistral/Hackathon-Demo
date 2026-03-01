import { useNavigate } from "react-router-dom";
import Footer from "../components/Footer";
import "./sass/Home.sass";

const Home = () => {
  const navigate = useNavigate();

  return (
    <div className="home">

      {/* HERO */}
      <section className="home__hero">
        <div className="home__overlay" />
        <div className="home__content">
          <h1>Welcome to PerrySphere</h1>
          <p>
            A multi-agent geopolitical simulation powered by advanced AI.
            Strategic reasoning driven by Mistral Large Language Models.
          </p>
          <button onClick={() => navigate("/map")}>
            Begin simulation
          </button>
        </div>
      </section>

      {/* ABOUT */}
      <section className="home__section">
        <h2>About the project</h2>
        <p>
          PerrySphere was developed for the Mistral Datathon (February 2026).
          It explores a multi-agent geopolitical world where countries act as
          autonomous AI-driven entities capable of strategic decision-making.
        </p>
        <p>
          Each country reasons independently and executes structured actions
          such as alliances, trade agreements, sanctions, or war declarations
          within a measurable world state.
        </p>
      </section>

      {/* PURPOSE */}
      <section className="home__section home__section--alt">
        <h2>Purpose</h2>
        <ul>
          <li>Design a multi-agent architecture driven by LLM reasoning</li>
          <li>Define a structured world state with measurable metrics</li>
          <li>Implement deterministic simulation rules with quantitative effects</li>
          <li>Build an interactive React frontend with real-time map visualization</li>
          <li>Experiment with hybrid control: AI reasoning + auditable rules</li>
        </ul>
      </section>

      {/* ARCHITECTURE */}
      <section className="home__section">
        <h2>High-Level architecture</h2>
        <div className="architecture">
          <div>
            <h3>Frontend</h3>
            <p>React-based UI with map visualization and real-time state updates.</p>
          </div>
          <div>
            <h3>API Layer</h3>
            <p>FastAPI endpoints to fetch world state and step the simulation.</p>
          </div>
          <div>
            <h3>Simulation Core</h3>
            <p>
              Multi-LLM agents select structured actions. A deterministic
              engine applies quantitative effects to update the world.
            </p>
          </div>
        </div>
      </section>

      {/* CORE CONCEPTS */}
      <section className="home__section home__section--alt">
        <h2>Core concepts</h2>
        <ul>
          <li><strong>WorldState</strong> – Global simulation representation</li>
          <li><strong>CountryState</strong> – Per-country metrics</li>
          <li><strong>RelationState</strong> – Bilateral relationship scores</li>
          <li><strong>ActionType</strong> – Structured diplomatic/military actions</li>
          <li><strong>Quantitative Effects</strong> – Bounded numerical impact</li>
        </ul>
      </section>

      {/* TECH STACK */}
      <section className="home__section">
        <h2>Tech stack</h2>
        <div className="tech">
          <span>React</span>
          <span>FastAPI</span>
          <span>Python</span>
          <span>Pydantic</span>
          <span>Asyncio</span>
          <span>Mistral LLM API</span>
        </div>
      </section>

      {/* FOOTER */}
      <Footer />

    </div>
  );
};

export default Home;