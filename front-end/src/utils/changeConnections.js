const getActionRelation = (connections, new_data) => {
    return connections.find((conn) => (conn.country_1 === new_data.source.id && conn.country_2 === new_data.target.id) 
        || (conn.country_1 === new_data.target.id && conn.country_2 === new_data.source.id))
}

const createNewConns = (connections, relation) => {
    let new_conns = connections.filter((conn) => conn.country_1 !== relation.country_1 || conn.country_2 !== relation.country_2)
    new_conns = [...new_conns, relation]

    return new_conns
}

const updateValues = (connections, setConnections, new_data) => {
    const relation = getActionRelation(connections, new_data)
    console.log("Relacion: ", relation)
    console.log("Data: ", new_data)
    relation.relation = new_data.metadata.relation
    console.log("Nueva relación: ", relation)
    const new_connections = createNewConns(connections, relation)
    console.log("Nuevas: ", new_connections)
    setConnections(new_connections)
}

export default updateValues
