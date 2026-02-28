import { MapContainer, TileLayer, Polyline, GeoJSON, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import worldGeo from '../assets/world.geo.json'

const WorldMapLeaflet = ({ countriesData, connections }) => {
    const countryStyle = {
        color: "#565656",
        weight: 3,
        fillColor: "#565656",
        fillOpacity: 0.2,
    }
    
    const selectedCountries = ["USA", "MEX", "BRA", "RUS"]
    const filteredGeo = {
        ...worldGeo,
            features: worldGeo.features.filter((feature) =>
                selectedCountries.includes(feature.properties.iso_a3)
            ),
    };

    const onEachFeature = (feature, layer) => {
        const map = useMap()
        const name = feature.properties.name;
        const population = feature.properties.pop_est;

        const popupContent = `<strong>${name}</strong><br/>
                                Population: ${population.toLocaleString()}<br/>
                                Economy: 25<br/>
                                Demography: 80<br/>
                                Military: 20<br/>
                                Technology: 60`
       
        let popup

        layer.on("mouseover", (e) => {
            e.target.setStyle({ weight: 4, color: "#457c4f", fillColor: "#457c4f" }); 
            popup = L.popup({ closeButton: false })
                .setLatLng(e.latlng)
                .setContent(popupContent)
                .openOn(map)
        });

        layer.on("mouseout", (e) => {
            e.target.setStyle(countryStyle);
            map.closePopup(popup);
        });
    };

    return (
        <>
            <MapContainer 
                center={[20, 0]} 
                minZoom={2}
                maxZoom={3}
                zoom={2} 
                zoomControl={false}
                style={{ height: '600px', width: '1200px' }} 
                worldCopyJump={false}
                maxBounds={[
                    [-90, -180], 
                    [90, 180]   
                ]}
                maxBoundsViscosity={1.0}
            >
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <GeoJSON data={filteredGeo} style={countryStyle} onEachFeature={onEachFeature}/>
                {connections.map((conn, idx) => (
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
