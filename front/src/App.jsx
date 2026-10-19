import { Navigate, Route, Routes } from 'react-router-dom';

import Layout from './components/Layout';
import CompanyDetailPage from './features/company/pages/detail/CompanyDetailPage';
import CompanyListPage from './features/company/pages/list/CompanyListPage';
import AboutPage from './pages/about/AboutPage';
import HomePage from './pages/home/HomePage';
import LoginPage from './pages/login/LoginPage';
import FinancialPage from './features/financial/pages/overview/FinancialPage';
import FinancialAssetsPage from './features/financial/pages/assets/FinancialAssetsPage';
import FinancialCreditPage from './features/financial/pages/credit/FinancialCreditPage';
import FinancialVehiclePage from './features/financial/pages/vehicle/FinancialVehiclePage';
import FinancialReviewPage from './features/financial/pages/review/FinancialReviewPage';
import FinancialResultPage from './features/financial/pages/result/FinancialResultPage';
import NotFound from './pages/not-found/NotFound';
import VehicleCatalogGate from './features/vehicle/components/VehicleCatalogGate';
import { VehicleProvider } from './features/vehicle/VehicleContext';
import { VehicleSearchPage } from './features/vehicle/pages/search/VehicleSearchPage';
import { VehicleResultsPage } from './features/vehicle/pages/results/VehicleResultsPage';
import VehicleDetailPage from './features/vehicle/pages/detail/VehicleDetailPage';
import VehicleComparePage from './features/vehicle/pages/compare/VehicleComparePage';
import VehicleSimulationPage from './features/vehicle/pages/simulation/VehicleSimulationPage';

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
        <Route path="/financial/credit" element={<FinancialCreditPage />} />
        <Route path="/financial/vehicle" element={<FinancialVehiclePage />} />
        <Route path="/financial/review" element={<FinancialReviewPage />} />
        <Route path="/financial/result" element={<FinancialResultPage />} />
        <Route path="/companies" element={<CompanyListPage />} />
        <Route path="/companies/:code" element={<CompanyDetailPage />} />
        <Route path="/search" element={<VehicleCatalogGate><VehicleSearchPage /></VehicleCatalogGate>} />
        <Route path="/vehicles" element={<VehicleCatalogGate><VehicleResultsPage /></VehicleCatalogGate>} />
        <Route path="/vehicles/compare" element={<VehicleCatalogGate><VehicleComparePage /></VehicleCatalogGate>} />
        <Route path="/vehicles/:id" element={<VehicleCatalogGate><VehicleDetailPage /></VehicleCatalogGate>} />
        <Route path="/vehicles/:id/simulation" element={<VehicleCatalogGate><VehicleSimulationPage /></VehicleCatalogGate>} />
        <Route path="/predict" element={<Navigate to="/financial" replace />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
    </VehicleProvider>
  );
}

export default App;
