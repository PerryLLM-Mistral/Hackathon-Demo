const BASE_URL = `${import.meta.env.VITE_PUBLIC_API_URL}/simulation/step`;

export async function useSimulation() {
    try {
        const response = await fetch(BASE_URL, {
            method: "POST",
        });

        if (!response.ok) {
            throw new Error("Failed to advance simulation");
        }

        const data = await response.json();
        return data;
    } catch (err) {
        throw new Error("Failed in simulation");
    } 
}

export default useSimulation;
