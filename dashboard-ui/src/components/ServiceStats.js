import React, { useEffect, useState } from 'react';
import '../App.css';

export default function ServiceStats() {
    const [isLoaded, setIsLoaded] = useState(false);
    const [healthStatus, setHealthStatus] = useState({});
    const [error, setError] = useState(null);

    const getHealthStatus = () => {
        fetch(`http://18.219.140.116:8120/health`) // Adjust the endpoint URL if needed
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
        const interval = setInterval(() => getHealthStatus(), 2000); // Update every 2 seconds
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
                    <li>Receiver: {healthStatus['receiver']}</li>
                    <li>Storage: {healthStatus['storage']}</li>
                    <li>Processing: {healthStatus['processing']}</li>
                    <li>Audit: {healthStatus['audit']}</li>
                </ul>
                <h3>Last Update: {healthStatus['last_update']}</h3>
            </div>
        );
    }
}