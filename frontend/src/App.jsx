import { useEffect, useState } from "react";
import { checkBackendHealth } from "./services/api";

function App() {
  const [backendStatus, setBackendStatus] = useState("Checking...");

  useEffect(() => {
    const checkConnection = async () => {
      try {
        const data = await checkBackendHealth();
        setBackendStatus(data.status);
      } catch (error) {
        console.error("Backend connection failed:", error);
        setBackendStatus("Backend unavailable");
      }
    };

    checkConnection();
  }, []);

  return (
    <div>
      <h1>Emergency Intelligence & Response</h1>

      <p>
        Backend status: <strong>{backendStatus}</strong>
      </p>
    </div>
  );
}

export default App;