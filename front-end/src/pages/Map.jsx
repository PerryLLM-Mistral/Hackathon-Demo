import './sass/Map.sass'
import WorldMapLeaflet from '../components/WorldMap'
import fetchCountries from '../hooks/countries'
import { useEffect, useState, useRef } from 'react'

const Map = () => {
    const [countries, setCountries] = useState([]);
    const [error, setError] = useState(null);
    const [messages, setMessages] = useState([
        {sender: "USA", content: "Hello!"},
        {sender: "USA", content: "How are you?"},
        {sender: "RUS", content: "This is a fixed-size chat. aaaaa aaaaaaa aaaaaaa aaaaaa aaaa"},
        {sender: "USA", content: "Hello!"},
        {sender: "USA", content: "How are you?"},
        {sender: "RUS", content: "This is a fixed-size chat. aaaaa aaaaaaa aaaaaaa aaaaaa aaaa"},
        {sender: "USA", content: "Hello!"},
        {sender: "USA", content: "How are you?"},
        {sender: "RUS", content: "This is a fixed-size chat. aaaaa aaaaaaa aaaaaaa aaaaaa aaaa"},
        {sender: "USA", content: "Hello!"},
        {sender: "USA", content: "How are you?"},
        {sender: "RUS", content: "This is a fixed-size chat. aaaaa aaaaaaa aaaaaaa aaaaaa aaaa"},
        {sender: "USA", content: "Hello!"},
        {sender: "USA", content: "How are you?"},
        {sender: "RUS", content: "This is a fixed-size chat. aaaaa aaaaaaa aaaaaaa aaaaaa aaaa"},
        {sender: "USA", content: "Hello!"},
        {sender: "USA", content: "How are you?"},
        {sender: "RUS", content: "This is a fixed-size chat. aaaaa aaaaaaa aaaaaaa aaaaaa aaaa"},
    ]);
    const hasFetched = useRef(false);

    useEffect(() => {
        if (hasFetched.current) return;
        hasFetched.current = true;

        async function getCountries() {
            try {
                const data = await fetchCountries();
                setCountries(data);
            } catch (err) {
                setError(err.message);
            }
        }

        getCountries();
    }, []);

    const connections = [
        { source: {id: "US", lat: 38.8977, lon: -77.0365}, target: {id: "MX", lat: 19.4326, lon: -99.1332}, color: "red", width: 2 },
        { source: {id: "US", lat: 38.8977, lon: -77.0365}, target: {id: "BR", lat: -15.7939, lon: -47.8828}, color: "orange", width: 3 },
        { source: {id: "MX", lat: 19.4326, lon: -99.1332}, target: {id: "BR", lat: -15.7939, lon: -47.8828}, color: "green", width: 1.5 }

    ];

    return (
        <div className="world-map">
            
            <section className="relations-map">
                <WorldMapLeaflet countriesData={countries} connections={connections} />
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
