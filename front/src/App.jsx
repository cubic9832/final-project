import { Route, Routes } from 'react-router-dom';

import Layout from './components/Layout';
import CompanyDetailPage from './pages/CompanyDetailPage';
import CompanyListPage from './pages/CompanyListPage';
import AboutPage from './pages/AboutPage';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import FinancialPage from './pages/FinancialPage';
import FinancialAssetsPage from './pages/FinancialAssetsPage';
import NotFound from './pages/NotFound';
import PredictPage from './pages/PredictPage';
import VehicleCatalogGate from './features/vehicle/VehicleCatalogGate';
import { VehicleProvider } from './features/vehicle/VehicleContext';
import { VehicleSearchPage, VehicleResultsPage } from './features/vehicle/VehicleSearchPage';
import VehicleDetailPage from './features/vehicle/VehicleDetailPage';
import VehicleComparePage from './features/vehicle/VehicleComparePage';
import VehicleSimulationPage from './features/vehicle/VehicleSimulationPage';

function App() {
  return (
    <VehicleProvider>
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/financial" element={<FinancialPage />} />
        <Route path="/financial/assets" element={<FinancialAssetsPage />} />
        <Route path="/companies" element={<CompanyListPage />} />
        <Route path="/companies/:code" element={<CompanyDetailPage />} />
        <Route path="/search" element={<VehicleCatalogGate><VehicleSearchPage /></VehicleCatalogGate>} />
        <Route path="/vehicles" element={<VehicleCatalogGate><VehicleResultsPage /></VehicleCatalogGate>} />
        <Route path="/vehicles/compare" element={<VehicleCatalogGate><VehicleComparePage /></VehicleCatalogGate>} />
        <Route path="/vehicles/:id" element={<VehicleCatalogGate><VehicleDetailPage /></VehicleCatalogGate>} />
        <Route path="/vehicles/:id/simulation" element={<VehicleCatalogGate><VehicleSimulationPage /></VehicleCatalogGate>} />
        <Route path="/predict" element={<PredictPage />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
    </VehicleProvider>
  );
}

export default App;
