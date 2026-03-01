const BASE_URL = `${import.meta.env.VITE_PUBLIC_API_URL}/countries/select-multiple`;

const selectMultipleCountries = async (countriesIds) => {
    try {
        const response = await fetch(BASE_URL, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(countriesIds),
        });

        if (!response.ok) {
            throw new Error("Error while selecting countries");
        }

        const data = await response.json();
        return data;
    } catch (err) {
        throw new Error("Error updating selected countries: ", err);
    }
}

export default selectMultipleCountries;