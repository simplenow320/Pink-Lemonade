import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';

const OrganizationOnboarding = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [orgData, setOrgData] = useState({
    name: '',
    legal_name: '',
    ein: '',
    org_type: '',
    year_founded: '',
    website: '',
    mission: '',
    vision: '',
    primary_focus_areas: [],
    service_area_type: '',
    primary_city: '',
    primary_state: '',
    primary_zip: '',
    annual_budget_range: '',
    staff_size: '',
    people_served_annually: '',
    programs_services: '',
    target_demographics: [],
    faith_based: false,
    minority_led: false,
    woman_led: false
  });

  const { user, updateOrganization, refetchOrganization } = useAuth();
  const navigate = useNavigate();

  const totalSteps = 4;

  // Pre-fill organization name if available from user registration
  useEffect(() => {
    if (user && user.org_name) {
      setOrgData(prev => ({
        ...prev,
        name: user.org_name
      }));
    }
  }, [user]);

  const handleInputChange = (field, value) => {
    setOrgData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleArrayChange = (field, value, checked) => {
    setOrgData(prev => ({
      ...prev,
      [field]: checked 
        ? [...prev[field], value]
        : prev[field].filter(item => item !== value)
    }));
  };

  const validateStep = (step) => {
    switch (step) {
      case 1:
        return orgData.name && orgData.org_type && orgData.mission;
      case 2:
        return orgData.primary_focus_areas.length > 0 && orgData.service_area_type;
      case 3:
        return orgData.annual_budget_range && orgData.staff_size;
      case 4:
        return true; // Optional step
      default:
        return false;
    }
  };

  const nextStep = () => {
    if (validateStep(currentStep) && currentStep < totalSteps) {
      setCurrentStep(prev => prev + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/organizations/profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(orgData),
      });

      const data = await response.json();

      if (response.ok) {
        updateOrganization(data);
        await refetchOrganization();
        navigate('/dashboard');
      } else {
        setError(data.error || 'Failed to save organization profile');
      }
    } catch (error) {
      setError('Failed to save organization profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Basic Information</h2>
              <p className="text-gray-600">Tell us about your organization</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Organization Name *
              </label>
              <input
                type="text"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                value={orgData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                placeholder="Your organization's name"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Legal Name (if different)
              </label>
              <input
                type="text"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                value={orgData.legal_name}
                onChange={(e) => handleInputChange('legal_name', e.target.value)}
                placeholder="Legal registered name"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Organization Type *
                </label>
                <select
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                  value={orgData.org_type}
                  onChange={(e) => handleInputChange('org_type', e.target.value)}
                  required
                >
                  <option value="">Select type...</option>
                  <option value="501c3">501(c)(3) Nonprofit</option>
                  <option value="faith-based">Faith-Based Organization</option>
                  <option value="educational">Educational Institution</option>
                  <option value="community">Community Organization</option>
                  <option value="healthcare">Healthcare Organization</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Year Founded
                </label>
                <input
                  type="number"
                  min="1800"
                  max={new Date().getFullYear()}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                  value={orgData.year_founded}
                  onChange={(e) => handleInputChange('year_founded', e.target.value)}
                  placeholder="YYYY"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                EIN / Tax ID
              </label>
              <input
                type="text"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                value={orgData.ein}
                onChange={(e) => handleInputChange('ein', e.target.value)}
                placeholder="XX-XXXXXXX"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Mission Statement *
              </label>
              <textarea
                rows="4"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                value={orgData.mission}
                onChange={(e) => handleInputChange('mission', e.target.value)}
                placeholder="Describe your organization's mission and purpose"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Vision Statement
              </label>
              <textarea
                rows="3"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                value={orgData.vision}
                onChange={(e) => handleInputChange('vision', e.target.value)}
                placeholder="Your organization's vision for the future"
              />
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Focus Areas & Geography</h2>
              <p className="text-gray-600">What does your organization focus on and where?</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Primary Focus Areas * (Select all that apply)
              </label>
              <div className="grid grid-cols-2 gap-3">
                {[
                  'Education', 'Healthcare', 'Housing', 'Food Security', 'Youth Development',
                  'Seniors', 'Arts & Culture', 'Environment', 'Economic Development',
                  'Mental Health', 'Substance Abuse', 'Criminal Justice', 'Immigration',
                  'LGBTQ+', 'Women\'s Issues', 'Veterans', 'Disability Services', 'Faith-Based'
                ].map(area => (
                  <label key={area} className="flex items-center">
                    <input
                      type="checkbox"
                      className="h-4 w-4 text-pink-600 focus:ring-pink-500 border-gray-300 rounded"
                      checked={orgData.primary_focus_areas.includes(area)}
                      onChange={(e) => handleArrayChange('primary_focus_areas', area, e.target.checked)}
                    />
                    <span className="ml-2 text-sm text-gray-700">{area}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Service Area Type *
              </label>
              <select
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                value={orgData.service_area_type}
                onChange={(e) => handleInputChange('service_area_type', e.target.value)}
                required
              >
                <option value="">Select service area...</option>
                <option value="local">Local (City/County)</option>
                <option value="regional">Regional (Multi-County)</option>
                <option value="statewide">Statewide</option>
                <option value="national">National</option>
                <option value="international">International</option>
              </select>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Primary City
                </label>
                <input
                  type="text"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                  value={orgData.primary_city}
                  onChange={(e) => handleInputChange('primary_city', e.target.value)}
                  placeholder="City"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  State
                </label>
                <input
                  type="text"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                  value={orgData.primary_state}
                  onChange={(e) => handleInputChange('primary_state', e.target.value)}
                  placeholder="State"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  ZIP Code
                </label>
                <input
                  type="text"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                  value={orgData.primary_zip}
                  onChange={(e) => handleInputChange('primary_zip', e.target.value)}
                  placeholder="ZIP"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Target Demographics (Select all that apply)
              </label>
              <div className="grid grid-cols-2 gap-3">
                {[
                  'Children (0-12)', 'Youth (13-18)', 'Young Adults (19-25)', 'Adults (26-64)',
                  'Seniors (65+)', 'Families', 'Single Parents', 'Veterans', 'Immigrants',
                  'Homeless', 'Low-Income', 'People with Disabilities'
                ].map(demo => (
                  <label key={demo} className="flex items-center">
                    <input
                      type="checkbox"
                      className="h-4 w-4 text-pink-600 focus:ring-pink-500 border-gray-300 rounded"
                      checked={orgData.target_demographics.includes(demo)}
                      onChange={(e) => handleArrayChange('target_demographics', demo, e.target.checked)}
                    />
                    <span className="ml-2 text-sm text-gray-700">{demo}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Organizational Capacity</h2>
              <p className="text-gray-600">Help us understand your organization's size and capacity</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Annual Budget Range *
                </label>
                <select
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                  value={orgData.annual_budget_range}
                  onChange={(e) => handleInputChange('annual_budget_range', e.target.value)}
                  required
                >
                  <option value="">Select budget range...</option>
                  <option value="under-100k">Under $100,000</option>
                  <option value="100k-500k">$100,000 - $500,000</option>
                  <option value="500k-1m">$500,000 - $1 Million</option>
                  <option value="1m-5m">$1 Million - $5 Million</option>
                  <option value="over-5m">Over $5 Million</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Staff Size *
                </label>
                <select
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                  value={orgData.staff_size}
                  onChange={(e) => handleInputChange('staff_size', e.target.value)}
                  required
                >
                  <option value="">Select staff size...</option>
                  <option value="1-5">1-5 employees</option>
                  <option value="6-10">6-10 employees</option>
                  <option value="11-25">11-25 employees</option>
                  <option value="26-50">26-50 employees</option>
                  <option value="over-50">Over 50 employees</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                People Served Annually
              </label>
              <input
                type="text"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                value={orgData.people_served_annually}
                onChange={(e) => handleInputChange('people_served_annually', e.target.value)}
                placeholder="e.g., 500-1000, Over 5000"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Programs & Services
              </label>
              <textarea
                rows="4"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                value={orgData.programs_services}
                onChange={(e) => handleInputChange('programs_services', e.target.value)}
                placeholder="Describe your key programs and services"
              />
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Additional Information</h2>
              <p className="text-gray-600">Help us better match you with relevant opportunities</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Website
              </label>
              <input
                type="url"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                value={orgData.website}
                onChange={(e) => handleInputChange('website', e.target.value)}
                placeholder="https://your-website.org"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Organization Characteristics
              </label>
              <div className="space-y-3">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    className="h-4 w-4 text-pink-600 focus:ring-pink-500 border-gray-300 rounded"
                    checked={orgData.faith_based}
                    onChange={(e) => handleInputChange('faith_based', e.target.checked)}
                  />
                  <span className="ml-2 text-sm text-gray-700">Faith-based organization</span>
                </label>

                <label className="flex items-center">
                  <input
                    type="checkbox"
                    className="h-4 w-4 text-pink-600 focus:ring-pink-500 border-gray-300 rounded"
                    checked={orgData.minority_led}
                    onChange={(e) => handleInputChange('minority_led', e.target.checked)}
                  />
                  <span className="ml-2 text-sm text-gray-700">Minority-led organization</span>
                </label>

                <label className="flex items-center">
                  <input
                    type="checkbox"
                    className="h-4 w-4 text-pink-600 focus:ring-pink-500 border-gray-300 rounded"
                    checked={orgData.woman_led}
                    onChange={(e) => handleInputChange('woman_led', e.target.checked)}
                  />
                  <span className="ml-2 text-sm text-gray-700">Woman-led organization</span>
                </label>
              </div>
            </div>

            <div className="bg-pink-50 border border-pink-200 rounded-lg p-4">
              <h3 className="font-medium text-pink-900 mb-2">Almost Done!</h3>
              <p className="text-sm text-pink-700">
                Your organization profile will help our AI match you with the most relevant grants and funding opportunities. 
                You can always update this information later from your dashboard.
              </p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-white py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Step {currentStep} of {totalSteps}
            </span>
            <span className="text-sm text-gray-500">
              {Math.round((currentStep / totalSteps) * 100)}% Complete
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <motion.div 
              className="bg-gradient-to-r from-pink-500 to-pink-600 h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${(currentStep / totalSteps) * 100}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>

        {/* Form Content */}
        <motion.div 
          className="bg-white rounded-xl shadow-lg p-8"
          key={currentStep}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          {renderStep()}

          {/* Navigation Buttons */}
          <div className="flex justify-between pt-8 border-t mt-8">
            <button
              type="button"
              onClick={prevStep}
              disabled={currentStep === 1}
              className={`px-6 py-2 rounded-lg font-medium ${
                currentStep === 1
                  ? 'text-gray-400 cursor-not-allowed'
                  : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              Previous
            </button>

            {currentStep < totalSteps ? (
              <button
                type="button"
                onClick={nextStep}
                disabled={!validateStep(currentStep)}
                className={`px-6 py-2 rounded-lg font-medium ${
                  validateStep(currentStep)
                    ? 'bg-gradient-to-r from-pink-500 to-pink-600 text-white hover:from-pink-600 hover:to-pink-700'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                Next
              </button>
            ) : (
              <button
                type="button"
                onClick={handleSubmit}
                disabled={loading}
                className={`px-6 py-2 rounded-lg font-medium ${
                  loading
                    ? 'bg-gray-400 text-white cursor-not-allowed'
                    : 'bg-gradient-to-r from-pink-500 to-pink-600 text-white hover:from-pink-600 hover:to-pink-700'
                }`}
              >
                {loading ? 'Saving...' : 'Complete Setup'}
              </button>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default OrganizationOnboarding;