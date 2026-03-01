import { useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import Footer from "../components/Footer";
import "./sass/Home.sass";

const Home = () => {
  const navigate = useNavigate();

  const rules = useMemo(
    () => [
      {
        title: "Game setup",
        items: [
          "Select five countries to play a match.",
          "The simulation starts with initial metrics and bilateral relations.",
        ],
      },
      {
        title: "Turn system",
        items: [
          "Advance the game by clicking “Next turn”.",
          "Each turn, one country agent selects a single structured action.",
        ],
      },
      {
        title: "Consequences",
        items: [
          "Actions have quantitative effects on relationships and metrics.",
          "Examples: ALLIANCE, SANCTION, WAR (bounded impact).",
        ],
      },
    ],
    []
  );

  const handleScrollTo = (id) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  // ---- reveal-on-scroll (IntersectionObserver)
  useEffect(() => {
    const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
    if (reduceMotion) return;

    const els = Array.from(document.querySelectorAll(".reveal"));
    if (!els.length) return;

    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) {
            e.target.classList.add("is-visible");
            io.unobserve(e.target);
          }
        }
      },
      { threshold: 0.15, rootMargin: "0px 0px -10% 0px" }
    );

    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);

  return (
    <div className="home">
      {/* HERO */}
      <section className="home__hero" aria-label="Hero">
        <div className="home__overlay" />
        <div className="home__container home__heroContent">
          <div className="home__heroText">
            <p className="home__kicker hero-in hero-in--1">
              Multi-agent geopolitical simulation
            </p>

            <h1 className="home__title hero-in hero-in--2">PerrySphere</h1>

            <p className="home__subtitle hero-in hero-in--3">
              Strategic decision-making by country agents powered by Mistral LLMs,
              enforced by deterministic, auditable rules.
            </p>

            <div className="home__ctaRow hero-in hero-in--4">
              <button
                className="home__button home__button--primary"
                onClick={() => navigate("/map")}
              >
                Start simulation
              </button>

              <button
                type="button"
                className="home__button home__button--ghost"
                onClick={() => handleScrollTo("how-it-works")}
              >
                How it works
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ABOUT */}
      <section className="home__section reveal" aria-label="About">
        <div className="home__container">
          <header className="home__sectionHeader reveal">
            <h2 className="home__h2">About the project</h2>
            <p className="home__lead">
              Built for the Mistral Datathon (February 2026), PerrySphere simulates a
              geopolitical world where countries behave as autonomous agents.
            </p>
          </header>

          <div className="home__grid2">
            <div className="home__card reveal reveal--1">
              <h3 className="home__h3">Agents</h3>
              <p className="home__text">
                Each country reasons independently and selects one structured action per
                turn (alliances, trade, sanctions, war).
              </p>
            </div>

            <div className="home__card reveal reveal--2">
              <h3 className="home__h3">World state</h3>
              <p className="home__text">
                Decisions are applied to a measurable world state with explicit metrics
                and bounded quantitative effects.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section
        id="how-it-works"
        className="home__section home__section--alt reveal"
        aria-label="How it works"
      >
        <div className="home__container">
          <header className="home__sectionHeader reveal">
            <h2 className="home__h2">How it works</h2>
            <p className="home__lead">
              A simple flow: pick countries, step through turns, observe measurable outcomes.
            </p>
          </header>

          <div className="home__grid3">
            <div className="home__stepCard reveal reveal--1">
              <div className="home__stepBadge">1</div>
              <h3 className="home__h3">Select 5 countries</h3>
              <p className="home__text">
                Choose the participants for the match. The simulation initializes metrics and relations.
              </p>
            </div>

            <div className="home__stepCard reveal reveal--2">
              <div className="home__stepBadge">2</div>
              <h3 className="home__h3">Step the simulation</h3>
              <p className="home__text">
                Click <strong>Next turn</strong> to advance. Each agent acts once per turn.
              </p>
            </div>

            <div className="home__stepCard reveal reveal--3">
              <div className="home__stepBadge">3</div>
              <h3 className="home__h3">Quantitative consequences</h3>
              <p className="home__text">
                Actions (ALLIANCE, WAR, SANCTION, etc.) update relations and metrics with bounded impact.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* GAME RULES */}
      <section className="home__section reveal" aria-label="Game rules">
        <div className="home__container">
          <header className="home__sectionHeader reveal">
            <h2 className="home__h2">Game rules</h2>
            <p className="home__lead">
              The simulation is turn-based and controlled. Outcomes are deterministic once an action is chosen.
            </p>
          </header>

          <div className="home__grid3">
            {rules.map((block, i) => (
              <div
                key={block.title}
                className={`home__card reveal reveal--${i + 1}`}
              >
                <h3 className="home__h3">{block.title}</h3>
                <ul className="home__list">
                  {block.items.map((item) => (
                    <li key={item} className="home__listItem">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="home__note reveal" role="note">
            <strong>Note:</strong> Relationship scores are bounded (e.g., from -100 to +100) to keep the system stable.
          </div>
        </div>
      </section>

      {/* PURPOSE */}
      <section className="home__section home__section--alt reveal" aria-label="Purpose">
        <div className="home__container">
          <header className="home__sectionHeader reveal">
            <h2 className="home__h2">Purpose</h2>
            <p className="home__lead">
              A hybrid design: LLM reasoning for strategy, deterministic rules for reproducibility and auditability.
            </p>
          </header>

          <div className="home__grid2">
            <div className="home__card reveal reveal--1">
              <h3 className="home__h3">What we built</h3>
              <ul className="home__list">
                <li className="home__listItem">Multi-agent architecture driven by LLM reasoning</li>
                <li className="home__listItem">Structured world state with measurable metrics</li>
                <li className="home__listItem">Deterministic simulation rules with quantitative effects</li>
              </ul>
            </div>

            <div className="home__card reveal reveal--2">
              <h3 className="home__h3">Why it matters</h3>
              <ul className="home__list">
                <li className="home__listItem">Transparent state updates and bounded impacts</li>
                <li className="home__listItem">Interactive frontend with real-time map visualization</li>
                <li className="home__listItem">Clear separation: reasoning vs. enforcement</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ARCHITECTURE */}
      <section className="home__section reveal" aria-label="Architecture">
        <div className="home__container">
          <header className="home__sectionHeader reveal">
            <h2 className="home__h2">High-level architecture</h2>
            <p className="home__lead">
              Three layers: UI, API, and a core simulation engine that applies effects.
            </p>
          </header>

          <div className="home__grid3">
            <div className="home__card reveal reveal--1">
              <h3 className="home__h3">Frontend</h3>
              <p className="home__text">
                React UI with map visualization and real-time state updates.
              </p>
            </div>

            <div className="home__card reveal reveal--2">
              <h3 className="home__h3">API layer</h3>
              <p className="home__text">
                FastAPI endpoints to fetch world state and step the simulation.
              </p>
            </div>

            <div className="home__card reveal reveal--3">
              <h3 className="home__h3">Simulation core</h3>
              <p className="home__text">
                LLM agents choose actions; a deterministic engine applies quantitative effects to update the world.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CORE CONCEPTS */}
      <section className="home__section home__section--alt reveal" aria-label="Core concepts">
        <div className="home__container">
          <header className="home__sectionHeader reveal">
            <h2 className="home__h2">Core concepts</h2>
            <p className="home__lead">
              The simulation is defined by explicit state objects and structured actions.
            </p>
          </header>

          <div className="home__grid2">
            <div className="home__card reveal reveal--1">
              <ul className="home__list">
                <li className="home__listItem">
                  <strong>WorldState</strong> — Global simulation representation
                </li>
                <li className="home__listItem">
                  <strong>CountryState</strong> — Per-country metrics
                </li>
                <li className="home__listItem">
                  <strong>RelationState</strong> — Bilateral relationship scores
                </li>
              </ul>
            </div>

            <div className="home__card reveal reveal--2">
              <ul className="home__list">
                <li className="home__listItem">
                  <strong>ActionType</strong> — Structured diplomatic/military actions
                </li>
                <li className="home__listItem">
                  <strong>Quantitative effects</strong> — Bounded numerical impact
                </li>
                <li className="home__listItem">
                  <strong>Turn-based loop</strong> — Controlled step progression
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* TECH STACK */}
      <section className="home__section reveal" aria-label="Tech stack">
        <div className="home__container">
          <header className="home__sectionHeader reveal">
            <h2 className="home__h2">Tech stack</h2>
          </header>

          <div className="home__tech reveal">
            <span className="home__chip">React</span>
            <span className="home__chip">FastAPI</span>
            <span className="home__chip">Python</span>
            <span className="home__chip">Pydantic</span>
            <span className="home__chip">Asyncio</span>
            <span className="home__chip">Mistral LLM API</span>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Home;