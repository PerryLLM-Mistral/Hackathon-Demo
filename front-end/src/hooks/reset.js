const BASE_URL = `${import.meta.env.VITE_PUBLIC_API_URL}/reset`;

const resetCountries = async () => {
    try {
        const response = await fetch(`${BASE_URL}/reset`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            }
        });

        if (!response.ok) {
            throw new Error("Error while reseting the countries");
        }
        const data = response.json();
        return data;
    } catch (err) {
        throw new Error("Error reseting")
    }
}

export default resetCountries
