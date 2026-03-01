import { useState, useEffect } from 'react';

const useWebSocket = () => {
    const [msg, setMsg] = useState(null);

    useEffect(() => {
        const WS_URL = import.meta.env.VITE_PUBLIC_API_URL.replace("http", "ws") + "/ws";
        const socket = new WebSocket(WS_URL);

        socket.onmessage = (event) => {
            const rawData = JSON.parse(event.data);
            const data = rawData.payload || rawData;

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
                        intensity: data.intensity
                    }
                };

                setMsg(organizedMsg);
            }
        };

        return () => socket.close();
    }, [WS_URL]);

    return msg; 
};

export default useWebSocket;