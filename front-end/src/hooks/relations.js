const BASE_URL = `${import.meta.env.VITE_PUBLIC_API_URL}/relationships`;

const fetchAllRelations = async () => {
    try {
        const response = await fetch(BASE_URL);
        if (!response.ok) {
            throw new Error("Error while fetching relations");
        }
        const data = await response.json();
        return data;
    } catch (err) {
        throw new Error("Error fetching relations");
    }
}

export default fetchAllRelations
