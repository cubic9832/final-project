import { Navigate, useLocation } from 'react-router-dom';

// Preserve bookmarked routes and saved inputs from the former separate step.
export default function FinancialAssetsPage() {
  const { state } = useLocation();
  return <Navigate to="/financial" state={state} replace />;
}
