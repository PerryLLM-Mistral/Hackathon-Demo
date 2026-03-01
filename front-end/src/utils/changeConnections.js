const getActionRelation = (connections, new_data) => {
    return connections.find((conn) => (conn.country_1 === new_data.agent && conn.country_2 === new_data.target) 
        || (conn.country_1 === new_data.target && conn.country_2 === new_data.agent))
}

const updateValues = (connections, setConnections, new_data) => {
    const relation = getActionRelation(connections, new_data)

    relation.relation = new_data.new_relation
}
