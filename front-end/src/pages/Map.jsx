import './sass/Map.sass'
import WorldMapLeaflet from '../components/WorldMap'
import WorldMapSelection from '../components/SelectCountryMap'
import fetchCountries from '../hooks/countries'
import fetchAllRelations from '../hooks/relations'
import cleanConns from '../utils/cleanConnections'
import useWebSocket from '../hooks/webSocket'
import useSimulation from '../hooks/useSimulation'
import updateValues from '../utils/changeConnections'
import changeValues from '../utils/changeCountries'
import { useEffect, useState, useRef } from 'react'
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const Map = () => {
    const [countries, setCountries] = useState([]);
    const [selectedCountries, setSelectedCountries] = useState([]);
    const [connections, setConnections] = useState([]);
    const [messages, setMessages] = useState([]);
    const [loadingMessages, setLoadingMessages] = useState(false);
    const [error, setError] = useState(null);
    const hasFetched = useRef(false);
    const msg = useWebSocket();

    useEffect(() => {
        if (!msg) return;
        setMessages(prev => [...prev, {
            sender: msg.source.id,
            target: msg.target.id,
            action: msg.metadata.actionType,
            content: msg.metadata.reason,
        }]);
        updateValues(connections, setConnections, msg);
        changeValues(countries, setSelectedCountries, msg.source);
        changeValues(countries, setSelectedCountries, msg.target);
        setLoadingMessages(false);
    }, [msg]);

    useEffect(() => {
        if (hasFetched.current) return;
        hasFetched.current = true;

        async function fetchData() {
            try {
                const data_countries = await fetchCountries();
                const data_relations = await fetchAllRelations();

                setCountries(data_countries);
                setConnections(data_relations);
            } catch (err) {
                setError(err.message);
            }
        }

        fetchData();
    }, []);

    const startSimulation = async () => {
        if (selectedCountries.length == 0) { 
            toast.error("Select 5 countries");
            return;
        } else if (loadingMessages) {
            toast.error("Wait until the previous messages load");
            return;
        }
        setLoadingMessages(true);
        const data = await useSimulation();
    }

    return (
        <div className="world-map">

            <section className="relations-map">
                {selectedCountries.length > 0 ? (
                    <WorldMapLeaflet countriesData={selectedCountries} connections={connections} />) : (
                    <WorldMapSelection countriesData={countries} setCountries={setSelectedCountries} />)
                }
            </section>
            <section className="bot-chat">
                <div className="chat-box">
                    <div className="chat-header">
                        <span className="chat-title">Actions</span>
                        <span className="chat-count">{messages.length} actions</span>
                    </div>

                    {messages.length == 0 && !loadingMessages && (
                        <p className="message">No messages generated</p>
                    )}
                    
                    {messages.map((msg, idx) => {
                        const hasTarget = msg.target && msg.target.length > 0;
                        const actionClass = `badge badge--${String(msg.action).toLowerCase()}`;

                        return (
                            <div key={idx} className="message">
                                <div className="msg-line1">
                                    <span className="msg-index">#{idx + 1}</span>

                                    <span className="msg-route">
                                        <strong className="msg-sender">{msg.sender}</strong>

                                        {hasTarget && (
                                            <>
                                                <span className="msg-arrow" aria-hidden="true">➜</span>
                                                <strong className="msg-target">{msg.target}</strong>
                                            </>
                                        )}
                                    </span>

                                    <span className={`badge badge--${String(msg.action).toLowerCase()}`}>
                                        {msg.action}
                                    </span>
                                </div>

                                <p className="msg-body">{msg.content}</p>
                            </div>
                        );
                    })}
                    
                    {loadingMessages && (
                        <p className="message">Loading messages...</p>
                    )}
                </div>

                <div className="simulation">
                    <button onClick={startSimulation}>Step Simulation</button>
                </div>
            </section>
            <ToastContainer position="top-right" autoClose={3000} />
        </div>
    )
}

export default Map
