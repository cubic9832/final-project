import { createContext, useContext } from 'react';

export const VehicleContext = createContext(null);
export function useVehicle() { return useContext(VehicleContext); }
