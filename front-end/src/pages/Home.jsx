import WorldMapLeaflet from '../components/WorldMap'

const Home = () => {
    const countriesData = [
        { id: "US", name: "United States", lat: 38.8977, lon: -77.0365, color: "blue", size: 6 },
        { id: "MX", name: "Mexico", lat: 19.4326, lon: -99.1332, color: "green", size: 5 },
        { id: "BR", name: "Brazil", lat: -15.7939, lon: -47.8828, color: "yellow", size: 7 }
    ];

    const connections = [
        { source: {id: "US", lat: 38.8977, lon: -77.0365}, target: {id: "MX", lat: 19.4326, lon: -99.1332}, color: "red", width: 2 },
        { source: {id: "US", lat: 38.8977, lon: -77.0365}, target: {id: "BR", lat: -15.7939, lon: -47.8828}, color: "orange", width: 3 },
        { source: {id: "MX", lat: 19.4326, lon: -99.1332}, target: {id: "BR", lat: -15.7939, lon: -47.8828}, color: "green", width: 1.5 }

    ];

    return (
        <>
            <section>
                <h1>Home</h1>
            </section>
        </>
    )
}

export default Home
