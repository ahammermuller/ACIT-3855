import React, { useEffect, useState } from 'react';
import '../App.css';

export default function ServiceStats() {
    const [isLoaded, setIsLoaded] = useState(false);
    const [health, setHealthStatus] = useState({});
    const [error, setError] = useState(null);

    const getHealthStatus = () => {
        fetch(`http://18.219.140.116:8120/health`)
            .then(res => res.json())
            .then(
                (result) => {
                    console.log("Received Health Status");
                    setHealthStatus(result);
                    setIsLoaded(true);
                },
                (error) => {
                    setError(error);
                    setIsLoaded(true);
                }
            );
    };

    useEffect(() => {
        const interval = setInterval(() => getHealthStatus(), 2000);
        return () => clearInterval(interval);
    }, [getHealthStatus]);

    if (error) {
        return <div className={"error"}>Error found when fetching from API</div>;
    } else if (isLoaded === false) {
        return <div>Loading...</div>;
    } else if (isLoaded === true) {
        return (
            <div>
                <h1>Health Status</h1>
                <ul>
                    <li>Receiver: {health['receiver']}</li>
                    <li>Storage: {health['storage']}</li>
                    <li>Processing: {health['processing']}</li>
                    <li>Audit: {health['audit']}</li>
                </ul>
                <h3>Last Update: {health['last_update']}</h3>
            </div>
        );
    }
}