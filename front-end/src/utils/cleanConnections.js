const getCountryData = (iso_a3, countries) => {
    return countries.find((c) => c.id === iso_a3)
}

const getRelationColor = (relation) => {
    if (relation < -20)
        return "#da3e3e"
    else if (relation > 20)
        return "#4eda3e"
    else
        return "#dacb3e"
}

const calcRelationWidth = (relation) => {
    return Math.round(Math.abs(relation) / 20) 
}

const getConnsFromCountries = (connections, countries) => {
    const countries_ids = countries.map((c) => c.id)
    const countries_conns = connections.filter((conn) => countries_ids.includes(conn.country_1) && countries_ids.includes(conn.country_2))

    return countries_conns
}

const cleanConns = (connections, countries) => {
    const countries_connections = getConnsFromCountries(connections, countries)
    return countries_connections.map((c) => {
        const country_1 = getCountryData(c.country_1, countries)
        const country_2 = getCountryData(c.country_2, countries)

        const color = getRelationColor(c.relation)
        const width = calcRelationWidth(c.relation)

        return {source: {id: country_1.id, lat: country_1.latitude, lon: country_1.longitude}, target: {id: country_2.id, lat: country_2.latitude, lon: country_2.longitude}, color: color, width: width}
    })
}

export default cleanConns
