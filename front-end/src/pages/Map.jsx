import './sass/Map.sass'
import WorldMapLeaflet from '../components/WorldMap'
import WorldMapSelection from '../components/SelectCountryMap'
import fetchCountries from '../hooks/countries'
import fetchAllRelations from '../hooks/relations'
import cleanConns from '../utils/cleanConnections'
import useWebSocket from '../hooks/webSocket'
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
        console.log(msg);
        setMessages(prev => [...prev, {sender: msg.source.id, content: msg.metadata.reason}])
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
                        <p key={idx} className="message"><strong>{msg.sender} </strong>{msg.content}</p>
                    ))}
                </div>
                <div className="simulation">
                    <button>Start Simulation</button>
                </div>
            </section>
        </div>
    )
}

export default Map
