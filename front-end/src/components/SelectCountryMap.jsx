import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Polyline, GeoJSON } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import resetCountries from '../hooks/reset'
import worldGeo from '../assets/world.geo.json'

const WorldMapSelection = ({ countriesData, setCountries }) => {
    const [selectedCountries, setSelectedCountries] = useState([])
    const countryStyle = {
        color: "#152242",
        weight: 3,
        fillColor: "#152242",
        fillOpacity: 0.2,
    }
    let simulationCountries = [];

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
        let selected = false;

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
            if (selected) return;
            layer.setStyle({
                weight: 4,
                color: "#05aab3",
                fillColor: "#05aab3"
            });
        });

        layer.on("click", function (e) {
            if (!selected) {
                simulationCountries.push(country)
                selected = true;
                layer.setStyle({
                    weight: 4,
                    color: "#c23917",
                    fillColor: "#c23917",
                });
            } else {
                simulationCountries = simulationCountries.filter((c) => c.id !== country.id)
                selected = false;
                layer.setStyle({                    
                    weight: 4,
                    color: "#05aab3",
                    fillColor: "#05aab3"
                })
            }
            console.log(simulationCountries);
        });

        layer.on("mouseout", function () {
            if (selected) return;
            layer.setStyle(countryStyle);
        });
    };

    const sendCountries = async () => {
        if (simulationCountries.length < 5 || simulationCountries.length > 5) {
            console.log(simulationCountries.length);
            alert("Select only 5 countries");
            return;
        }

        const reset = await resetCountries();
        setCountries(simulationCountries);
    }

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
            </MapContainer>
            <button
                style={{
                    position: 'absolute',
                    top: '2%',
                    right: '22%',
                    zIndex: 1000, // importante para que esté encima del mapa
                    padding: '8px 12px',
                    backgroundColor: '#05aab3',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                }}
                onClick={sendCountries}
            >
                Select Countries
            </button>
        </>
    );
};

export default WorldMapSelection;
