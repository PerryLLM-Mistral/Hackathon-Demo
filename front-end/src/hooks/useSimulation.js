// src/hooks/useSimulation.js

import { useState } from "react";

const BASE_URL = `${import.meta.env.VITE_PUBLIC_API_URL}/step`;

export function useSimulation() {
    const [loading, setLoading] = useState(false);
    const [lastDelta, setLastDelta] = useState(null);
    const [error, setError] = useState(null);

    const step = async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await fetch(BASE_URL, {
                method: "POST",
            });

            if (!response.ok) {
                throw new Error("Failed to advance simulation");
            }

            const data = await response.json();
            setLastDelta(data);
            return data;
        } catch (err) {
            setError(err);
        } finally {
            setLoading(false);
        }
    };

    return { step, loading, lastDelta, error };
}