import React, { useEffect, useState } from 'react'
import '../App.css';

export default function AppStats() {
    const [isLoaded, setIsLoaded] = useState(false);
    const [stats, setStats] = useState({});
    const [error, setError] = useState(null)

	const getStats = () => {
	
        fetch(`http://18.219.140.116:8100/stats`)
            .then(res => res.json())
            .then((result)=>{
				console.log("Received Stats")
                setStats(result);
                setIsLoaded(true);
            },(error) =>{
                setError(error)
                setIsLoaded(true);
            })
    }
    useEffect(() => {
		const interval = setInterval(() => getStats(), 2000); // Update every 2 seconds
		return() => clearInterval(interval);
    }, [getStats]);

    if (error){
        return (<div className={"error"}>Error found when fetching from API</div>)
    } else if (isLoaded === false){
        return(<div>Loading...</div>)
    } else if (isLoaded === true){
        return(
            <div>
                <h1>Latest Stats</h1>
                <table className={"StatsTable"}>
					<tbody>
						<tr>
							<th>Distance Covered</th>
							<th>Running Pace</th>
						</tr>
						<tr>
							<td># DC: {stats['num_distance_events_received']}</td>
							<td># RP: {stats['num_pace_events_received']}</td>
						</tr>
						<tr>
							<td colspan="2">Total Distance Covered: {stats['total_distance_covered']} kilometers</td>
						</tr>
						<tr>
							<td colspan="2">Average Pace: {stats['average_pace']} minutes per kilometer</td>
						</tr>
						<tr>
							<td colspan="2">Max Elevation: {stats['max_elevation']} meters</td>
						</tr>
					</tbody>
                </table>
                <h3>Last Updated: {stats['last_timestamp']}</h3>

            </div>
        )
    }
}
