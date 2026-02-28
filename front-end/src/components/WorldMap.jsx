import { MapContainer, TileLayer, CircleMarker, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const WorldMapLeaflet = ({ countriesData, connections }) => {
    return (
        <>
            <MapContainer 
                center={[20, 0]} 
                minZoom={2}
                zoom={2} 
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
                {countriesData.map((c, idx) => (
                    <CircleMarker
                        key={idx}
                        center={[c.lat, c.lon]}
                        radius={5}
                        pathOptions={{ color: c.color || 'red' }}
                    />
                ))}
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
