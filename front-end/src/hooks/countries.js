const BASE_URL = `${import.meta.env.VITE_PUBLIC_API_URL}/countries`;

const fetchCountries = async () => {
    try {
        const response = await fetch(BASE_URL)
        if (!response.ok) {
            console.log("Error")
            throw new Error("Error while fetching countries")
        }
        const data = await response.json()
        return data
    } catch (err) {
        throw new Error("Error fetching countries")
    }
}

export default fetchCountries
