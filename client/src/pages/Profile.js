import React, { useState, useEffect } from 'react';
import { UserIcon, EnvelopeIcon, PhoneIcon, BriefcaseIcon, BuildingOfficeIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';
import ProgressIndicator from '../components/ui/ProgressIndicator';
import ProfileRewards from '../components/ui/ProfileRewards';
import ErrorVisualization from '../components/ui/ErrorVisualization';

const Profile = () => {
  const [profileData, setProfileData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    job_title: '',
    org_name: '',
    timezone: 'America/New_York',
    notification_preferences: {
      email_notifications: true,
      grant_alerts: true,
      weekly_digest: true,
      deadline_reminders: true
    }
  });
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [errors, setErrors] = useState({});
  const [profileCompletion, setProfileCompletion] = useState(0);

  // Fetch user profile on mount
  useEffect(() => {
    fetchProfile();
  }, []);

  // Calculate profile completion whenever profileData changes
  useEffect(() => {
    calculateCompletion();
  }, [profileData]);

  const fetchProfile = async () => {
    try {
      const response = await fetch('/api/profile/get', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.profile) {
          setProfileData(prevData => ({
            ...prevData,
            ...data.profile,
            notification_preferences: {
              ...prevData.notification_preferences,
              ...data.profile.notification_preferences
            }
          }));
        }
      } else if (response.status === 401) {
        window.location.href = '/';
      }
    } catch (error) {
      console.error('Error fetching profile:', error);
      setMessage({ type: 'error', text: 'Failed to load profile' });
    } finally {
      setLoading(false);
    }
  };

  const calculateCompletion = () => {
    const fields = ['first_name', 'last_name', 'email', 'phone', 'job_title', 'org_name'];
    const filledFields = fields.filter(field => profileData[field] && profileData[field].trim() !== '');
    const completion = Math.round((filledFields.length / fields.length) * 100);
    setProfileCompletion(completion);
  };

  const handleInputChange = (field, value) => {
    setProfileData(prev => ({
      ...prev,
      [field]: value
    }));
    // Clear error for this field
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  const handleNotificationChange = (pref, value) => {
    setProfileData(prev => ({
      ...prev,
      notification_preferences: {
        ...prev.notification_preferences,
        [pref]: value
      }
    }));
  };

  const validateProfile = () => {
    const newErrors = {};
    
    if (!profileData.first_name?.trim()) {
      newErrors.first_name = 'First name is required';
    }
    
    if (!profileData.last_name?.trim()) {
      newErrors.last_name = 'Last name is required';
    }
    
    if (!profileData.email?.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profileData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    
    if (profileData.phone && !/^[\d\s\-\(\)\+]+$/.test(profileData.phone)) {
      newErrors.phone = 'Please enter a valid phone number';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validateProfile()) {
      setMessage({ type: 'error', text: 'Please fix the errors below' });
      return;
    }

    setSaving(true);
    setMessage({ type: '', text: '' });

    try {
      const response = await fetch('/api/profile/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(profileData)
      });

      const data = await response.json();

      if (response.ok) {
        setMessage({ type: 'success', text: 'Profile updated successfully!' });
        // Update profile data with response
        if (data.profile) {
          setProfileData(prev => ({
            ...prev,
            ...data.profile
          }));
        }
      } else {
        setMessage({ type: 'error', text: data.error || 'Failed to update profile' });
      }
    } catch (error) {
      console.error('Error saving profile:', error);
      setMessage({ type: 'error', text: 'Failed to save profile. Please try again.' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-500"></div>
      </div>
    );
  }

  const completedSections = [];
  if (profileData.first_name && profileData.last_name) completedSections.push('personal_info');
  if (profileData.email && profileData.phone) completedSections.push('contact_info');
  if (profileData.job_title && profileData.org_name) completedSections.push('work_info');
  if (profileCompletion >= 100) completedSections.push('profile_complete');

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">My Profile</h1>
        <p className="mt-2 text-sm text-gray-600">
          Manage your personal information and preferences
        </p>
      </div>

      {/* Progress and Rewards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
        <div className="lg:col-span-2">
          <ProgressIndicator 
            currentStep={Math.ceil(profileCompletion / 25)}
            totalSteps={4}
            percentage={profileCompletion}
            title="Profile Completion"
          />
        </div>
        <div>
          <ProfileRewards 
            completedSections={completedSections}
            totalXP={completedSections.length * 100}
          />
        </div>
      </div>

      {/* Message Display */}
      {message.text && (
        <div className={`mb-6 p-4 rounded-lg flex items-center ${
          message.type === 'success' 
            ? 'bg-green-50 text-green-800 border border-green-200' 
            : 'bg-red-50 text-red-800 border border-red-200'
        }`}>
          {message.type === 'success' ? (
            <CheckCircleIcon className="h-5 w-5 mr-2" />
          ) : (
            <XCircleIcon className="h-5 w-5 mr-2" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      {/* Profile Form */}
      <div className="bg-white shadow-lg rounded-lg">
        <div className="p-6 space-y-8">
          {/* Personal Information */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <UserIcon className="h-5 w-5 mr-2 text-pink-500" />
              Personal Information
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  First Name *
                </label>
                <input
                  type="text"
                  value={profileData.first_name}
                  onChange={(e) => handleInputChange('first_name', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500 ${
                    errors.first_name ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="John"
                />
                {errors.first_name && (
                  <p className="mt-1 text-sm text-red-600">{errors.first_name}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Last Name *
                </label>
                <input
                  type="text"
                  value={profileData.last_name}
                  onChange={(e) => handleInputChange('last_name', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500 ${
                    errors.last_name ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="Doe"
                />
                {errors.last_name && (
                  <p className="mt-1 text-sm text-red-600">{errors.last_name}</p>
                )}
              </div>
            </div>
          </div>

          {/* Contact Information */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <EnvelopeIcon className="h-5 w-5 mr-2 text-pink-500" />
              Contact Information
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address *
                </label>
                <input
                  type="email"
                  value={profileData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500 ${
                    errors.email ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="john@example.com"
                />
                {errors.email && (
                  <p className="mt-1 text-sm text-red-600">{errors.email}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center">
                  <PhoneIcon className="h-4 w-4 mr-1" />
                  Phone Number
                </label>
                <input
                  type="tel"
                  value={profileData.phone}
                  onChange={(e) => handleInputChange('phone', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500 ${
                    errors.phone ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="(555) 123-4567"
                />
                {errors.phone && (
                  <p className="mt-1 text-sm text-red-600">{errors.phone}</p>
                )}
              </div>
            </div>
          </div>

          {/* Work Information */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <BriefcaseIcon className="h-5 w-5 mr-2 text-pink-500" />
              Work Information
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center">
                  <BriefcaseIcon className="h-4 w-4 mr-1" />
                  Job Title
                </label>
                <input
                  type="text"
                  value={profileData.job_title}
                  onChange={(e) => handleInputChange('job_title', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                  placeholder="Grant Manager"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center">
                  <BuildingOfficeIcon className="h-4 w-4 mr-1" />
                  Organization
                </label>
                <input
                  type="text"
                  value={profileData.org_name}
                  onChange={(e) => handleInputChange('org_name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                  placeholder="Urban Hope Foundation"
                />
              </div>
            </div>
          </div>

          {/* Preferences */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Notification Preferences
            </h2>
            <div className="space-y-3">
              {[
                { key: 'email_notifications', label: 'Email Notifications', desc: 'Receive updates via email' },
                { key: 'grant_alerts', label: 'Grant Alerts', desc: 'Get notified about new matching grants' },
                { key: 'weekly_digest', label: 'Weekly Digest', desc: 'Receive a weekly summary of activity' },
                { key: 'deadline_reminders', label: 'Deadline Reminders', desc: 'Get reminded of upcoming grant deadlines' }
              ].map(pref => (
                <label key={pref.key} className="flex items-start">
                  <input
                    type="checkbox"
                    checked={profileData.notification_preferences[pref.key]}
                    onChange={(e) => handleNotificationChange(pref.key, e.target.checked)}
                    className="mt-1 h-4 w-4 text-pink-600 focus:ring-pink-500 border-gray-300 rounded"
                  />
                  <div className="ml-3">
                    <span className="text-sm font-medium text-gray-700">{pref.label}</span>
                    <p className="text-xs text-gray-500">{pref.desc}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Timezone */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Timezone
            </label>
            <select
              value={profileData.timezone}
              onChange={(e) => handleInputChange('timezone', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
            >
              <option value="America/New_York">Eastern Time</option>
              <option value="America/Chicago">Central Time</option>
              <option value="America/Denver">Mountain Time</option>
              <option value="America/Los_Angeles">Pacific Time</option>
            </select>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end space-x-3">
          <button
            onClick={fetchProfile}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-pink-500"
            disabled={saving}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 text-sm font-medium text-white bg-pink-600 border border-transparent rounded-lg hover:bg-pink-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-pink-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Profile;