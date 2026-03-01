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

const Map = () => {
    const [countries, setCountries] = useState([]);
    const [selectedCountries, setSelectedCountries] = useState([]);
    const [connections, setConnections] = useState([]);
    const [messages, setMessages] = useState([]);
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
        }])
        updateValues(connections, setConnections, msg)
        changeValues(countries, setSelectedCountries, msg.source)
        changeValues(countries, setSelectedCountries, msg.target)
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
        const data = await useSimulation();
    }
    
    return (
        <div className="world-map">
            
            <section className="relations-map">
                {selectedCountries.length > 0 ? (
                    <WorldMapLeaflet countriesData={selectedCountries} connections={connections} />) : (
                    <WorldMapSelection countriesData={countries} setCountries={setSelectedCountries}/>)
                }
            </section>
            <section className="bot-chat">
                <div className="chat-box">
                    {messages.length == 0 && 
                        <p className="message">No messages generated</p>
                    }
                    {messages.map((msg, idx) =>(
                        msg.target.length == 0 ? ( 
                            <p key={idx} className="message"><strong>{msg.sender}<br/>{msg.action} </strong>{msg.content}</p>) : (
                            <p key={idx} className="message"><strong>{msg.sender}->{msg.target}<br/>{msg.action} </strong>{msg.content}</p>)
                    ))}
                </div>
                <div className="simulation">
                    <button onClick={startSimulation}>Step Simulation</button>
                </div>
            </section>
        </div>
    )
}

export default Map
