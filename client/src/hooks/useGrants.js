import { useState, useEffect, useCallback } from 'react';
import { getGrants, getDashboardData } from '../utils/api';

export function useGrants(filters = {}) {
  const [grants, setGrants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);

  // Fetch grants
  const fetchGrants = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getGrants(filters);
      setGrants(data);
      setError(null);
    } catch (err) {
      console.error('Error fetching grants:', err);
      setError('Failed to fetch grants. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // Fetch dashboard data
  const fetchDashboardData = useCallback(async () => {
    try {
      const data = await getDashboardData();
      setDashboardData(data);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      // We don't set error state here to avoid blocking the UI
    }
  }, []);

  // Load grants on mount and when filters change
  useEffect(() => {
    fetchGrants();
  }, [fetchGrants]);

  // Load dashboard data if requested
  useEffect(() => {
    if (filters.includeDashboard) {
      fetchDashboardData();
    }
  }, [fetchDashboardData, filters.includeDashboard]);

  // Function to refresh data
  const refreshData = useCallback(() => {
    fetchGrants();
    if (filters.includeDashboard) {
      fetchDashboardData();
    }
  }, [fetchGrants, fetchDashboardData, filters.includeDashboard]);

  return {
    grants,
    loading,
    error,
    refreshData,
    dashboardData
  };
}

export default useGrants;
