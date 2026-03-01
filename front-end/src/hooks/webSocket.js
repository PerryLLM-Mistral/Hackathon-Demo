import { useState, useEffect, useRef } from "react";

const useWebSocket = () => {
    const [msg, setMsg] = useState(null);
    const socketRef = useRef(null);

    useEffect(() => {
        if (socketRef.current) return;
        let apiUrl = import.meta.env.VITE_PUBLIC_API_URL;
        if (!apiUrl) return;

        // Convert HTTP/HTTPS to WS/WSS safely
        const WS_URL =
            apiUrl.startsWith("https")
                ? apiUrl.replace("https", "wss") + "/ws"
                : apiUrl.replace("http", "ws") + "/ws";

        const socket = new WebSocket(WS_URL);

        socket.onopen = () => {
            console.log("WebSocket connected");
        };

        socket.onmessage = (event) => {
            try {
                const rawData = JSON.parse(event.data);
                const data = rawData.payload?.data || rawData.payload || rawData.data || rawData;
                

                if (data.type === "AGENT_ACTION") {
                    const organizedMsg = {
                        source: {
                            id: data.agent,
                            economy: data.actor_stats?.economy,
                            military: data.actor_stats?.military,
                            social: data.actor_stats?.social,
                            demography: data.actor_stats?.demography,
                            technology: data.actor_stats?.technology,
                        },
                        target: {
                            id: data.target,
                            economy: data.target_stats?.economy,
                            military: data.target_stats?.military,
                            social: data.target_stats?.social,
                            demography: data.target_stats?.demography,
                            technology: data.target_stats?.technology,
                        },
                        metadata: {
                            actionType: data.action_type,
                            relation: data.new_relation,
                            reason: data.reason,
                            intensity: data.intensity,
                        },
                    };
                    setMsg(organizedMsg);
                }
            } catch (e) {
                console.error("Failed to parse WebSocket message:", e);
            }
        };

        socket.onerror = (err) => {
            console.error("WebSocket error:", err);
        };

        socket.onclose = (e) => {
            console.log("WebSocket closed:", e);
        };

        // Cleanup on unmount
        return () => {
            console.log("Closing WebSocket");
            socket.close();
        };
    }, []);

    return msg;
};

export default useWebSocket;
