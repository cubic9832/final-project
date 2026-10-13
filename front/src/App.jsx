import { Route, Routes } from 'react-router-dom';

import Layout from './components/Layout';
import CompanyDetailPage from './pages/CompanyDetailPage';
import CompanyListPage from './pages/CompanyListPage';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import FinancialPage from './pages/FinancialPage';
import FinancialAssetsPage from './pages/FinancialAssetsPage';
import FinancialCreditPage from './pages/FinancialCreditPage';
import FinancialVehiclePage from './pages/FinancialVehiclePage';
import NotFound from './pages/NotFound';
import PredictPage from './pages/PredictPage';
import SearchPage from './pages/SearchPage';

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/financial" element={<FinancialPage />} />
        <Route path="/financial/assets" element={<FinancialAssetsPage />} />
        <Route path="/financial/credit" element={<FinancialCreditPage />} />
        <Route path="/financial/vehicle" element={<FinancialVehiclePage />} />
        <Route path="/companies" element={<CompanyListPage />} />
        <Route path="/companies/:code" element={<CompanyDetailPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/predict" element={<PredictPage />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

export default App;
