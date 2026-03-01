import { useEffect, useState, useMemo } from 'react'
import { MapContainer, TileLayer, Polyline, GeoJSON } from 'react-leaflet'
import cleanConns from '../utils/cleanConnections'
import 'leaflet/dist/leaflet.css'
import worldGeo from '../assets/world.geo.json'

const WorldMapLeaflet = ({ countriesData, connections }) => {
    const [selectedCountries, setSelectedCountries] = useState([])
    const countryStyle = {
        color: "#152242",
        weight: 3,
        fillColor: "#152242",
        fillOpacity: 0.2,
    }

    const cleanConnections = useMemo(() => {
        if (!countriesData.length || !connections.length) return []
        let cleaned = cleanConns(connections, countriesData)
        cleaned = cleaned.filter((c) => c.relation > 20 || c.relation < -20)
        return cleaned
    }, [countriesData, connections])

    useEffect(() => {
        const ids = countriesData.map((country) => country.id)
        setSelectedCountries(ids)
    }, [countriesData])
    
    const filteredGeo = {
        ...worldGeo,
            features: worldGeo.features.filter((feature) =>
                selectedCountries.includes(feature.properties.adm0_a3)
            ),
    };

    const onEachFeature = (feature, layer) => {
        if (!countriesData) return;
        const name = feature.properties.name;
        const population = feature.properties.pop_est;
        const country = countriesData.find((c) => c.id === feature.properties.adm0_a3)

        const popupContent = `<strong>${name}</strong><br/>
                                Population: ${population.toLocaleString()}<br/>
                                Economy: ${country.economy}<br/>
                                Demography: ${country.demography}<br/>
                                Social: ${country.social}<br/>
                                Military: ${country.military_power}<br/>
                                Technology: ${country.technology}`
       
        layer.bindTooltip(popupContent, {
            sticky: true,
            direction: "bottom",
            opacity: 1,
            className: "custom-popup"
        });

        layer.on("mousemove", function (e) {
            layer.setStyle({
                weight: 4,
                color: "#05aab3",
                fillColor: "#05aab3"
            });
        });

        layer.on("mouseout", function () {
            layer.setStyle(countryStyle);
        });

    };

    return (
        <>
            <MapContainer 
                center={[20, 0]} 
                minZoom={2}
                maxZoom={5}
                zoom={2} 
                zoomControl={false}
                worldCopyJump={false}
                style={{ height: "92dvh", width: "80%" }}
                maxBounds={[
                    [-90, -180], 
                    [90, 180]   
                ]}
                maxBoundsViscosity={1.0}
            >
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <GeoJSON key={selectedCountries.join('-')} data={filteredGeo} style={countryStyle} onEachFeature={onEachFeature}/>
                {cleanConnections.map((conn, idx) => (
                    <Polyline
                        key={idx}
                        positions={[[conn.source.lat, conn.source.lon], [conn.target.lat, conn.target.lon]]}
                        pathOptions={{ color: conn.color || 'blue', weight: conn.width || 2 }}
                    />
                ))}
            </MapContainer>
        </>
    );
};

export default WorldMapLeaflet;
