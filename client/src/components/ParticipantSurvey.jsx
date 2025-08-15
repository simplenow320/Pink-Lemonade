import React, { useState } from 'react';

const ParticipantSurvey = () => {
  const [step, setStep] = useState(1);
  const [submitted, setSubmitted] = useState(false);
  const [confirmationCode, setConfirmationCode] = useState('');
  
  const [formData, setFormData] = useState({
    // Participant Info
    name: '',
    age: '',
    location: '',
    program: '',
    
    // Impact Questions
    impact_q1: '',
    impact_q2: '',
    impact_q3: 5,
    impact_q4: '',
    impact_q5: '',
    
    // Improvement Questions
    improve_q1: '',
    improve_q2: ''
  });

  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async () => {
    try {
      const response = await fetch('/api/phase5/survey/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          survey_id: new URLSearchParams(window.location.search).get('id') || 'default'
        })
      });
      
      const data = await response.json();
      if (data.success) {
        setConfirmationCode(data.confirmation_code);
        setSubmitted(true);
      } else {
        alert(data.error || 'Failed to submit survey');
      }
    } catch (error) {
      console.error('Error submitting survey:', error);
      alert('Error submitting survey. Please try again.');
    }
  };

  const nextStep = () => {
    if (step === 1) {
      // Validate participant info
      if (!formData.name || !formData.age || !formData.location || !formData.program) {
        alert('Please fill in all participant information');
        return;
      }
    }
    setStep(step + 1);
  };

  const prevStep = () => {
    setStep(step - 1);
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-pink-50 to-white flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
          <div className="mb-6">
            <svg className="w-20 h-20 mx-auto text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Thank You!</h2>
          <p className="text-gray-600 mb-6">
            Your feedback has been successfully submitted and will help us improve our programs.
          </p>
          <div className="bg-pink-50 rounded-lg p-4 mb-6">
            <p className="text-sm text-gray-500 mb-2">Confirmation Code</p>
            <p className="text-lg font-mono font-bold text-pink-600">{confirmationCode}</p>
          </div>
          <p className="text-sm text-gray-500">
            Please save this confirmation code for your records.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-white py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg">
          {/* Header */}
          <div className="bg-pink-500 text-white p-6 rounded-t-lg">
            <h1 className="text-2xl font-bold">Program Impact Survey</h1>
            <p className="mt-2">Your feedback helps us improve our programs</p>
          </div>

          {/* Progress Bar */}
          <div className="px-6 py-4 border-b">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-500">Step {step} of 3</span>
              <span className="text-sm text-gray-500">{Math.round((step / 3) * 100)}% Complete</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-pink-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(step / 3) * 100}%` }}
              />
            </div>
          </div>

          {/* Form Content */}
          <div className="p-6">
            {step === 1 && (
              <div className="space-y-4">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Participant Information</h2>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Your Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => handleChange('name', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
                    placeholder="Enter your full name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Your Age *
                  </label>
                  <input
                    type="number"
                    value={formData.age}
                    onChange={(e) => handleChange('age', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
                    placeholder="Enter your age"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Your Location *
                  </label>
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => handleChange('location', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
                    placeholder="City, State"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Program Enrolled *
                  </label>
                  <input
                    type="text"
                    value={formData.program}
                    onChange={(e) => handleChange('program', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
                    placeholder="Name of the program you participated in"
                  />
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="space-y-4">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Program Impact</h2>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    1. How has this program helped you?
                  </label>
                  <textarea
                    value={formData.impact_q1}
                    onChange={(e) => handleChange('impact_q1', e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
                    placeholder="Describe how the program has helped you..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    2. What specific changes have you experienced?
                  </label>
                  <textarea
                    value={formData.impact_q2}
                    onChange={(e) => handleChange('impact_q2', e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
                    placeholder="List any changes in your life since joining..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    3. Rate the program's impact on your life (1-10)
                  </label>
                  <div className="flex items-center space-x-2">
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(num => (
                      <button
                        key={num}
                        onClick={() => handleChange('impact_q3', num)}
                        className={`w-10 h-10 rounded-full ${
                          formData.impact_q3 === num
                            ? 'bg-pink-500 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {num}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    4. Would you recommend this program to others?
                  </label>
                  <select
                    value={formData.impact_q4}
                    onChange={(e) => handleChange('impact_q4', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
                  >
                    <option value="">Select an option</option>
                    <option value="Yes">Yes</option>
                    <option value="No">No</option>
                    <option value="Maybe">Maybe</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    5. What was the most valuable part of the program?
                  </label>
                  <textarea
                    value={formData.impact_q5}
                    onChange={(e) => handleChange('impact_q5', e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
                    placeholder="What did you value most..."
                  />
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="space-y-4">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Program Improvement</h2>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    1. How could this program better serve your needs?
                  </label>
                  <textarea
                    value={formData.improve_q1}
                    onChange={(e) => handleChange('improve_q1', e.target.value)}
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
                    placeholder="Suggest improvements or changes..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    2. Who else in your community could benefit from this program?
                  </label>
                  <textarea
                    value={formData.improve_q2}
                    onChange={(e) => handleChange('improve_q2', e.target.value)}
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-pink-500 focus:border-pink-500"
                    placeholder="Describe other people or groups who might benefit..."
                  />
                </div>
              </div>
            )}
          </div>

          {/* Navigation */}
          <div className="px-6 py-4 bg-gray-50 rounded-b-lg flex justify-between">
            <button
              onClick={prevStep}
              disabled={step === 1}
              className={`px-4 py-2 rounded-md ${
                step === 1
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-gray-300 text-gray-700 hover:bg-gray-400'
              }`}
            >
              Previous
            </button>
            
            {step < 3 ? (
              <button
                onClick={nextStep}
                className="px-4 py-2 bg-pink-500 text-white rounded-md hover:bg-pink-600"
              >
                Next
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                className="px-4 py-2 bg-pink-500 text-white rounded-md hover:bg-pink-600"
              >
                Submit Survey
              </button>
            )}
          </div>
        </div>

        {/* Help Text */}
        <div className="mt-4 text-center text-sm text-gray-500">
          <p>Need help? Contact support at support@pinklemonade.org</p>
        </div>
      </div>
    </div>
  );
};

export default ParticipantSurvey;