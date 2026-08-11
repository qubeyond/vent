import { Route, Routes } from "react-router-dom";
import { AuthProvider } from "./features/auth/AuthContext";
import { ProtectedRoute } from "./app/ProtectedRoute";
import { Layout } from "./app/Layout";
import { LoginPage } from "./pages/LoginPage";
import { DumpPage } from "./pages/DumpPage";
import { CloudPage } from "./pages/CloudPage";
import { StatsPage } from "./pages/StatsPage";
import { EntryPage } from "./pages/EntryPage";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<DumpPage />} />
          <Route path="/cloud" element={<CloudPage />} />
          <Route path="/stats" element={<StatsPage />} />
          <Route path="/entries/:id" element={<EntryPage />} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}
