import React, { useState, useEffect } from 'react';
import ProgressIndicator from '../components/ui/ProgressIndicator';
import ProfileRewards from '../components/ui/ProfileRewards';
import { FieldTooltip } from '../components/ui/Tooltip';
import ErrorVisualization from '../components/ui/ErrorVisualization';

const Organization = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({});
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [completionPercentage, setCompletionPercentage] = useState(15);

  // Mock completed sections for ProfileRewards
  const completedSections = ['basic_info'];

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user types
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  const validateStep = (step) => {
    const newErrors = {};
    
    if (step === 1) {
      if (!formData.legal_name) newErrors.legal_name = 'Organization name is required';
      if (!formData.org_type) newErrors.org_type = 'Organization type is required';
      if (formData.ein && !/^\d{2}-\d{7}$/.test(formData.ein)) {
        newErrors.ein = 'EIN must be in format XX-XXXXXXX';
      }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      if (currentStep < 5) {
        setCurrentStep(currentStep + 1);
        setCompletionPercentage(prev => Math.min(prev + 20, 100));
      }
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
            Organization Legal Name
            <FieldTooltip 
              label="Legal Name"
              description="The official name registered with the IRS"
              example="Urban Hope Foundation Inc."
              required={true}
            />
          </label>
          <input
            type="text"
            value={formData.legal_name || ''}
            onChange={(e) => handleInputChange('legal_name', e.target.value)}
            className={`form-input ${errors.legal_name ? 'border-red-300' : ''}`}
            placeholder="Enter your organization's legal name"
          />
          {errors.legal_name && (
            <ErrorVisualization
              type="validation"
              field="Organization Name"
              error={errors.legal_name}
              solution="Enter the full legal name as registered with the IRS."
            />
          )}
        </div>

        <div>
          <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
            EIN (Optional)
            <FieldTooltip 
              label="EIN"
              description="Your Employer Identification Number from the IRS"
              example="12-3456789"
            />
          </label>
          <input
            type="text"
            value={formData.ein || ''}
            onChange={(e) => handleInputChange('ein', e.target.value)}
            className={`form-input ${errors.ein ? 'border-red-300' : ''}`}
            placeholder="XX-XXXXXXX"
          />
          {errors.ein && (
            <ErrorVisualization
              type="format"
              field="EIN"
              error={errors.ein}
              solution="Use the format XX-XXXXXXX with numbers only."
            />
          )}
        </div>
      </div>

      <div>
        <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
          Organization Type
          <FieldTooltip 
            label="Organization Type"
            description="What type of nonprofit are you?"
            example="Faith-based, Community-based, Educational"
            required={true}
          />
        </label>
        <select
          value={formData.org_type || ''}
          onChange={(e) => handleInputChange('org_type', e.target.value)}
          className={`form-select ${errors.org_type ? 'border-red-300' : ''}`}
        >
          <option value="">Select organization type</option>
          <option value="faith_based">Faith-based</option>
          <option value="community_based">Community-based</option>
          <option value="educational">Educational</option>
          <option value="health">Health & Medical</option>
          <option value="environmental">Environmental</option>
          <option value="arts">Arts & Culture</option>
          <option value="social_services">Social Services</option>
        </select>
        {errors.org_type && (
          <ErrorVisualization
            type="validation"
            field="Organization Type"
            error={errors.org_type}
            solution="Please select the type that best describes your organization."
          />
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
            Year Founded
            <FieldTooltip 
              label="Year Founded"
              description="When was your organization officially started?"
              example="2015"
            />
          </label>
          <input
            type="number"
            value={formData.year_founded || ''}
            onChange={(e) => handleInputChange('year_founded', e.target.value)}
            className="form-input"
            placeholder="2020"
            min="1900"
            max="2025"
          />
        </div>

        <div>
          <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
            Website
            <FieldTooltip 
              label="Website"
              description="Your organization's main website"
              example="https://urbanhope.org"
            />
          </label>
          <input
            type="url"
            value={formData.website || ''}
            onChange={(e) => handleInputChange('website', e.target.value)}
            className="form-input"
            placeholder="https://yourorg.org"
          />
        </div>
      </div>

      <div>
        <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
          Mission Statement
          <FieldTooltip 
            label="Mission"
            description="Your organization's main purpose and goals"
            example="Empowering urban communities through education and support"
          />
        </label>
        <textarea
          value={formData.mission || ''}
          onChange={(e) => handleInputChange('mission', e.target.value)}
          className="form-input"
          rows="3"
          placeholder="Describe your organization's mission in simple terms..."
        />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { key: 'faith_based', label: 'Faith-based' },
          { key: 'minority_led', label: 'Minority-led' },
          { key: 'woman_led', label: 'Woman-led' },
          { key: 'veteran_led', label: 'Veteran-led' }
        ].map(({ key, label }) => (
          <label key={key} className="flex items-center">
            <input
              type="checkbox"
              checked={formData[key] || false}
              onChange={(e) => handleInputChange(key, e.target.checked)}
              className="form-checkbox"
            />
            <span className="ml-2 text-sm text-gray-700">{label}</span>
          </label>
        ))}
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div>
        <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
          Primary Focus Areas
          <FieldTooltip 
            label="Focus Areas"
            description="What areas does your organization focus on?"
            example="Education, Workforce Development, Community Health"
          />
        </label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {[
            'Education', 'Healthcare', 'Housing', 'Workforce Development',
            'Youth Development', 'Senior Services', 'Mental Health', 'Food Security',
            'Community Development', 'Arts & Culture', 'Environment', 'Justice'
          ].map(area => (
            <label key={area} className="flex items-center">
              <input
                type="checkbox"
                checked={formData.primary_focus_areas?.includes(area) || false}
                onChange={(e) => {
                  const current = formData.primary_focus_areas || [];
                  const updated = e.target.checked
                    ? [...current, area]
                    : current.filter(item => item !== area);
                  handleInputChange('primary_focus_areas', updated);
                }}
                className="form-checkbox"
              />
              <span className="ml-2 text-sm text-gray-700">{area}</span>
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
          Programs & Services
          <FieldTooltip 
            label="Programs"
            description="Describe the main programs and services you offer"
            example="After-school tutoring, job training academy, food pantry"
          />
        </label>
        <textarea
          value={formData.programs_services || ''}
          onChange={(e) => handleInputChange('programs_services', e.target.value)}
          className="form-input"
          rows="3"
          placeholder="Describe your main programs and services..."
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
            Primary City
            <FieldTooltip 
              label="Primary City"
              description="The main city where you operate"
              example="Atlanta"
            />
          </label>
          <input
            type="text"
            value={formData.primary_city || ''}
            onChange={(e) => handleInputChange('primary_city', e.target.value)}
            className="form-input"
            placeholder="City name"
          />
        </div>

        <div>
          <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
            Primary State
            <FieldTooltip 
              label="Primary State"
              description="The main state where you operate"
              example="Georgia"
            />
          </label>
          <select
            value={formData.primary_state || ''}
            onChange={(e) => handleInputChange('primary_state', e.target.value)}
            className="form-select"
          >
            <option value="">Select state</option>
            <option value="Alabama">Alabama</option>
            <option value="Georgia">Georgia</option>
            <option value="Florida">Florida</option>
            <option value="North Carolina">North Carolina</option>
            <option value="South Carolina">South Carolina</option>
            <option value="Tennessee">Tennessee</option>
            {/* Add more states as needed */}
          </select>
        </div>
      </div>
    </div>
  );

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return renderStep1();
      case 2:
        return renderStep2();
      case 3:
        return <div className="text-center py-8 text-gray-500">Step 3: Organizational Capacity (Coming Soon)</div>;
      case 4:
        return <div className="text-center py-8 text-gray-500">Step 4: Grant History (Coming Soon)</div>;
      case 5:
        return <div className="text-center py-8 text-gray-500">Step 5: AI Learning (Coming Soon)</div>;
      default:
        return renderStep1();
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900">Organization Profile Setup</h1>
        <p className="mt-2 text-gray-600">Tell us about your organization to get better grant matches</p>
      </div>

      {/* Progress Indicator */}
      <ProgressIndicator currentStep={currentStep} totalSteps={5} />

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Form Section */}
        <div className="lg:col-span-3">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">
              {currentStep === 1 && 'Basic Information'}
              {currentStep === 2 && 'Programs & Services'}
              {currentStep === 3 && 'Organizational Capacity'}
              {currentStep === 4 && 'Grant History'}
              {currentStep === 5 && 'AI Learning Settings'}
            </h2>

            {renderStepContent()}

            {/* Navigation Buttons */}
            <div className="flex justify-between mt-8 pt-6 border-t border-gray-200">
              <button
                onClick={handlePrevious}
                disabled={currentStep === 1}
                className={`px-6 py-2 rounded-lg font-medium transition-colors duration-200 ${
                  currentStep === 1
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Previous
              </button>

              <button
                onClick={handleNext}
                disabled={currentStep === 5}
                className={`px-6 py-2 rounded-lg font-medium transition-colors duration-200 ${
                  currentStep === 5
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-pink-500 text-white hover:bg-pink-600'
                }`}
              >
                {currentStep === 5 ? 'Complete' : 'Continue'}
              </button>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="lg:col-span-1">
          <ProfileRewards 
            completionPercentage={completionPercentage}
            completedSections={completedSections}
            totalSections={5}
          />
        </div>
      </div>
    </div>
  );
};

export default Organization;