import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckIcon, ChevronRightIcon, ChevronLeftIcon } from '@heroicons/react/24/outline';
import { motion, AnimatePresence } from 'framer-motion';
import ProgressIndicator from '../components/ui/ProgressIndicator';
import WelcomeAnimation from '../components/ui/WelcomeAnimation';

const Onboarding = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [userData, setUserData] = useState({
    first_name: '',
    last_name: '',
    phone: '',
    job_title: '',
    org_name: '',
    org_type: '',
    mission: '',
    primary_focus_areas: [],
    primary_city: '',
    primary_state: '',
    notification_preferences: {
      email_notifications: true,
      grant_alerts: true,
      weekly_digest: true,
      deadline_reminders: true
    }
  });
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const steps = [
    {
      id: 'welcome',
      title: 'Welcome to Pink Lemonade!',
      description: 'Let\'s get you set up in just a few minutes',
      component: StepWelcome
    },
    {
      id: 'personal',
      title: 'Personal Information',
      description: 'Tell us a bit about yourself',
      component: StepPersonal
    },
    {
      id: 'organization',
      title: 'Organization Details',
      description: 'Help us understand your organization',
      component: StepOrganization
    },
    {
      id: 'focus',
      title: 'Focus Areas',
      description: 'What areas does your organization focus on?',
      component: StepFocus
    },
    {
      id: 'preferences',
      title: 'Notification Preferences',
      description: 'How would you like to stay informed?',
      component: StepPreferences
    },
    {
      id: 'complete',
      title: 'All Set!',
      description: 'You\'re ready to start finding grants',
      component: StepComplete
    }
  ];

  const handleNext = async () => {
    if (currentStep === steps.length - 1) {
      // Complete onboarding
      await completeOnboarding();
    } else {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleSkip = () => {
    navigate('/dashboard');
  };

  const completeOnboarding = async () => {
    setSaving(true);
    try {
      // Save profile data
      const profileResponse = await fetch('/api/profile/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(userData)
      });

      if (profileResponse.ok) {
        // Mark onboarding as complete
        await fetch('/api/profile/onboarding/complete', {
          method: 'POST',
          credentials: 'include'
        });

        // Navigate to dashboard
        setTimeout(() => {
          navigate('/dashboard');
        }, 2000);
      }
    } catch (error) {
      console.error('Error completing onboarding:', error);
    } finally {
      setSaving(false);
    }
  };

  const CurrentStepComponent = steps[currentStep].component;

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-white">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Progress Bar */}
        <div className="mb-8">
          <ProgressIndicator
            currentStep={currentStep + 1}
            totalSteps={steps.length}
            percentage={((currentStep + 1) / steps.length) * 100}
            title="Getting Started"
          />
        </div>

        {/* Step Content */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          <div className="p-8">
            {/* Step Header */}
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-2">
                {steps[currentStep].title}
              </h2>
              <p className="text-gray-600">
                {steps[currentStep].description}
              </p>
            </div>

            {/* Step Component */}
            <AnimatePresence mode="wait">
              <motion.div
                key={currentStep}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                <CurrentStepComponent
                  userData={userData}
                  setUserData={setUserData}
                  errors={errors}
                  setErrors={setErrors}
                />
              </motion.div>
            </AnimatePresence>
          </div>

          {/* Navigation */}
          <div className="px-8 py-4 bg-gray-50 border-t border-gray-200 flex justify-between">
            <button
              onClick={handleBack}
              disabled={currentStep === 0}
              className={`flex items-center px-4 py-2 text-sm font-medium rounded-lg ${
                currentStep === 0
                  ? 'text-gray-400 cursor-not-allowed'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <ChevronLeftIcon className="h-4 w-4 mr-1" />
              Back
            </button>

            <button
              onClick={handleSkip}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Skip for now
            </button>

            <button
              onClick={handleNext}
              disabled={saving}
              className="flex items-center px-6 py-2 text-sm font-medium text-white bg-pink-600 rounded-lg hover:bg-pink-700 disabled:opacity-50"
            >
              {currentStep === steps.length - 1 ? (
                saving ? 'Completing...' : 'Complete Setup'
              ) : (
                <>
                  Next
                  <ChevronRightIcon className="h-4 w-4 ml-1" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Step Components
function StepWelcome() {
  return (
    <div className="text-center py-12">
      <WelcomeAnimation />
      <div className="mt-8 space-y-4">
        <p className="text-lg text-gray-700">
          Welcome to your AI-powered grant management platform!
        </p>
        <p className="text-gray-600">
          We'll help you discover, track, and apply for grants that match your organization's mission.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
          <div className="text-center">
            <div className="w-12 h-12 bg-pink-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-pink-600 font-bold">1</span>
            </div>
            <h3 className="font-semibold text-gray-900">Discover Grants</h3>
            <p className="text-sm text-gray-600 mt-1">
              AI-powered matching finds the best opportunities
            </p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-pink-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-pink-600 font-bold">2</span>
            </div>
            <h3 className="font-semibold text-gray-900">Track Progress</h3>
            <p className="text-sm text-gray-600 mt-1">
              Manage applications and deadlines in one place
            </p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-pink-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-pink-600 font-bold">3</span>
            </div>
            <h3 className="font-semibold text-gray-900">Win Funding</h3>
            <p className="text-sm text-gray-600 mt-1">
              AI helps write compelling grant proposals
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function StepPersonal({ userData, setUserData, errors }) {
  const handleChange = (field, value) => {
    setUserData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            First Name *
          </label>
          <input
            type="text"
            value={userData.first_name}
            onChange={(e) => handleChange('first_name', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
            placeholder="John"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Last Name *
          </label>
          <input
            type="text"
            value={userData.last_name}
            onChange={(e) => handleChange('last_name', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
            placeholder="Doe"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Phone Number
        </label>
        <input
          type="tel"
          value={userData.phone}
          onChange={(e) => handleChange('phone', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
          placeholder="(555) 123-4567"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Job Title
        </label>
        <input
          type="text"
          value={userData.job_title}
          onChange={(e) => handleChange('job_title', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
          placeholder="Executive Director"
        />
      </div>
    </div>
  );
}

function StepOrganization({ userData, setUserData }) {
  const handleChange = (field, value) => {
    setUserData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Organization Name *
        </label>
        <input
          type="text"
          value={userData.org_name}
          onChange={(e) => handleChange('org_name', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
          placeholder="Urban Hope Foundation"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Organization Type
        </label>
        <select
          value={userData.org_type}
          onChange={(e) => handleChange('org_type', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
        >
          <option value="">Select type</option>
          <option value="faith_based">Faith-based</option>
          <option value="community_based">Community-based</option>
          <option value="educational">Educational</option>
          <option value="health">Health & Medical</option>
          <option value="social_services">Social Services</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Mission Statement
        </label>
        <textarea
          value={userData.mission}
          onChange={(e) => handleChange('mission', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
          rows="3"
          placeholder="Describe your organization's mission..."
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            City
          </label>
          <input
            type="text"
            value={userData.primary_city}
            onChange={(e) => handleChange('primary_city', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
            placeholder="Atlanta"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            State
          </label>
          <input
            type="text"
            value={userData.primary_state}
            onChange={(e) => handleChange('primary_state', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
            placeholder="Georgia"
          />
        </div>
      </div>
    </div>
  );
}

function StepFocus({ userData, setUserData }) {
  const focusAreas = [
    'Education', 'Healthcare', 'Housing', 'Workforce Development',
    'Youth Development', 'Senior Services', 'Mental Health', 'Food Security',
    'Community Development', 'Arts & Culture', 'Environment', 'Justice',
    'Technology', 'Financial Literacy', 'Homelessness', 'Substance Abuse'
  ];

  const toggleFocusArea = (area) => {
    setUserData(prev => {
      const current = prev.primary_focus_areas || [];
      const updated = current.includes(area)
        ? current.filter(a => a !== area)
        : [...current, area];
      return { ...prev, primary_focus_areas: updated };
    });
  };

  return (
    <div className="space-y-6">
      <p className="text-gray-600">
        Select all areas that apply to your organization's work:
      </p>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {focusAreas.map(area => {
          const isSelected = userData.primary_focus_areas?.includes(area);
          return (
            <button
              key={area}
              onClick={() => toggleFocusArea(area)}
              className={`p-3 rounded-lg border-2 text-sm font-medium transition-all ${
                isSelected
                  ? 'border-pink-500 bg-pink-50 text-pink-700'
                  : 'border-gray-200 hover:border-gray-300 text-gray-700'
              }`}
            >
              <div className="flex items-center justify-between">
                <span>{area}</span>
                {isSelected && <CheckIcon className="h-4 w-4 ml-2" />}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function StepPreferences({ userData, setUserData }) {
  const handleToggle = (pref) => {
    setUserData(prev => ({
      ...prev,
      notification_preferences: {
        ...prev.notification_preferences,
        [pref]: !prev.notification_preferences[pref]
      }
    }));
  };

  const preferences = [
    {
      key: 'email_notifications',
      title: 'Email Notifications',
      description: 'Receive important updates via email'
    },
    {
      key: 'grant_alerts',
      title: 'Grant Alerts',
      description: 'Get notified when new matching grants are found'
    },
    {
      key: 'weekly_digest',
      title: 'Weekly Digest',
      description: 'Receive a weekly summary of grant opportunities'
    },
    {
      key: 'deadline_reminders',
      title: 'Deadline Reminders',
      description: 'Get reminded of upcoming grant deadlines'
    }
  ];

  return (
    <div className="space-y-4">
      <p className="text-gray-600 mb-6">
        Choose how you'd like to stay informed about grant opportunities:
      </p>
      {preferences.map(pref => (
        <div
          key={pref.key}
          className="flex items-start p-4 border border-gray-200 rounded-lg hover:border-gray-300"
        >
          <input
            type="checkbox"
            checked={userData.notification_preferences[pref.key]}
            onChange={() => handleToggle(pref.key)}
            className="mt-1 h-4 w-4 text-pink-600 focus:ring-pink-500 border-gray-300 rounded"
          />
          <div className="ml-3 flex-1">
            <label className="font-medium text-gray-900">
              {pref.title}
            </label>
            <p className="text-sm text-gray-600 mt-1">
              {pref.description}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

function StepComplete() {
  return (
    <div className="text-center py-12">
      <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
        <CheckIcon className="h-10 w-10 text-green-600" />
      </div>
      <h3 className="text-2xl font-bold text-gray-900 mb-3">
        You're All Set!
      </h3>
      <p className="text-gray-600 mb-8">
        Your profile is complete and you're ready to start discovering grants.
      </p>
      <div className="bg-pink-50 rounded-lg p-6 text-left max-w-md mx-auto">
        <h4 className="font-semibold text-gray-900 mb-3">What's Next?</h4>
        <ul className="space-y-2 text-sm text-gray-700">
          <li className="flex items-start">
            <CheckIcon className="h-4 w-4 text-pink-600 mr-2 mt-0.5" />
            <span>Explore the dashboard to see grant opportunities</span>
          </li>
          <li className="flex items-start">
            <CheckIcon className="h-4 w-4 text-pink-600 mr-2 mt-0.5" />
            <span>Complete your organization profile for better matching</span>
          </li>
          <li className="flex items-start">
            <CheckIcon className="h-4 w-4 text-pink-600 mr-2 mt-0.5" />
            <span>Set up grant tracking for your active applications</span>
          </li>
        </ul>
      </div>
    </div>
  );
}

export default Onboarding;