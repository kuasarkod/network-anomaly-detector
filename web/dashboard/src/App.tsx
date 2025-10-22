import { useEffect, useState } from "react";
import "./App.css";

type AnomalyRecord = {
  id: number;
  detected_at: string;
  score: number;
  description: string;
  event: {
    source_ip: string | null;
    destination_ip: string | null;
    protocol: string | null;
    destination_port: number | null;
  };
};

function App() {
  const [anomalies, setAnomalies] = useState<AnomalyRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8080/anomalies")
      .then((response) => response.json())
      .then((data) => setAnomalies(data))
      .catch(() => setAnomalies([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="App">Yükleniyor...</div>;
  }

  return (
    <div className="App">
      <h1>Network Anomaly Dashboard</h1>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Score</th>
            <th>Detay</th>
            <th>Kaynak</th>
            <th>Hedef</th>
            <th>Protokol</th>
          </tr>
        </thead>
        <tbody>
          {anomalies.map((anomaly) => (
            <tr key={anomaly.id}>
              <td>{anomaly.id}</td>
              <td>{anomaly.score.toFixed(2)}</td>
              <td>{anomaly.description}</td>
              <td>{anomaly.event.source_ip || "-"}</td>
              <td>{anomaly.event.destination_ip || "-"}</td>
              <td>{anomaly.event.protocol || "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;
