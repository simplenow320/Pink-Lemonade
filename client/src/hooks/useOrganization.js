import { useState, useEffect, useCallback } from 'react';
import { getOrganization, updateOrganization, seedOrganization } from '../utils/api';

export function useOrganization() {
  const [organization, setOrganization] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saveStatus, setSaveStatus] = useState(null);

  // Fetch organization
  const fetchOrganization = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getOrganization();
      setOrganization(data);
      setError(null);
    } catch (err) {
      console.error('Error fetching organization:', err);
      setError('Failed to fetch organization profile. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  // Update organization
  const saveOrganization = useCallback(async (orgData) => {
    setSaveStatus('saving');
    try {
      const updatedOrg = await updateOrganization(orgData);
      setOrganization(updatedOrg);
      setSaveStatus('success');
      setTimeout(() => setSaveStatus(null), 3000);
      return updatedOrg;
    } catch (err) {
      console.error('Error updating organization:', err);
      setSaveStatus('error');
      throw err;
    }
  }, []);

  // Seed organization with sample data
  const initializeSampleOrganization = useCallback(async () => {
    setLoading(true);
    try {
      const data = await seedOrganization();
      setOrganization(data.data);
      setError(null);
      return data;
    } catch (err) {
      console.error('Error seeding organization:', err);
      setError('Failed to seed organization profile. Please try again.');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Load organization on mount
  useEffect(() => {
    fetchOrganization();
  }, [fetchOrganization]);

  return {
    organization,
    loading,
    error,
    saveOrganization,
    initializeSampleOrganization,
    saveStatus,
    refreshOrganization: fetchOrganization,
  };
}

export default useOrganization;
