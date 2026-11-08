import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import "./index.css";
import "./lib/i18n";
import { AuthProvider } from "./lib/auth";
import { PublicLayout } from "./components/PublicLayout";
import Landing from "./pages/Landing";
import Report from "./pages/Report";
import TrackDetail, { TrackLookup } from "./pages/Track";
import Login from "./pages/Login";
import ControlRoom from "./pages/ControlRoom";
import Admin from "./pages/Admin";
import Crew from "./pages/Crew";

function NotFound() {
  return <div className="mx-auto max-w-xl p-12"><h1 className="text-2xl font-bold">Page not found</h1><a className="btn-text mt-4" href="/">Go to the home page</a></div>;
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route element={<PublicLayout />}>
            <Route index element={<Landing />} />
            <Route path="report" element={<Report />} />
            <Route path="track" element={<TrackLookup />} />
            <Route path="track/:id" element={<TrackDetail />} />
            <Route path="login" element={<Login />} />
            <Route path="*" element={<NotFound />} />
          </Route>
          <Route path="ops" element={<ControlRoom />} />
          <Route path="ops/:id" element={<ControlRoom />} />
          <Route path="admin" element={<Admin />} />
          <Route path="crew/:unitId" element={<Crew />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
