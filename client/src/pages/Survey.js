import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';

const Survey = () => {
  const { projectId } = useParams();
  const [searchParams] = useSearchParams();
  const role = searchParams.get('role') || 'participant';
  
  const [survey, setSurvey] = useState(null);
  const [responses, setResponses] = useState({});
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [completed, setCompleted] = useState(false);

  useEffect(() => {
    loadSurvey();
  }, [projectId, role]);

  const loadSurvey = async () => {
    try {
      const response = await fetch(`/api/smart-reporting/phase3/survey/${projectId}?role=${role}`);
      const data = await response.json();
      
      if (data.success) {
        setSurvey(data.survey);
      } else {
        console.error('Failed to load survey:', data.error);
      }
    } catch (error) {
      console.error('Survey loading error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleResponse = (questionId, value) => {
    setResponses(prev => ({
      ...prev,
      [questionId]: value
    }));
  };

  const submitSurvey = async () => {
    setSubmitting(true);
    try {
      const response = await fetch(`/api/smart-reporting/phase3/survey-response`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: parseInt(projectId),
          respondent_role: role,
          responses: responses
        })
      });

      const data = await response.json();
      if (data.success) {
        setCompleted(true);
      } else {
        alert('Failed to submit survey: ' + data.error);
      }
    } catch (error) {
      console.error('Survey submission error:', error);
      alert('Failed to submit survey. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading survey...</p>
        </div>
      </div>
    );
  }

  if (completed) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <motion.div 
          className="max-w-md mx-auto bg-white rounded-lg shadow-lg p-8 text-center"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <div className="text-6xl mb-4">🎉</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Thank You!</h1>
          <p className="text-gray-600 mb-6">
            Your survey response has been submitted successfully. Your input is valuable for measuring program impact.
          </p>
          <div className="bg-pink-50 border border-pink-200 rounded-lg p-4">
            <p className="text-pink-800 text-sm">
              You can close this window. If you have questions, contact us at support@pinklemonade.app
            </p>
          </div>
        </motion.div>
      </div>
    );
  }

  if (!survey || !survey.questions || survey.questions.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="max-w-md mx-auto bg-white rounded-lg shadow-lg p-8 text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Survey Not Available</h1>
          <p className="text-gray-600 mb-6">
            The survey you're looking for is not available or has been completed.
          </p>
        </div>
      </div>
    );
  }

  const progress = ((currentQuestion + 1) / survey.questions.length) * 100;
  const question = survey.questions[currentQuestion];

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">🍋 Impact Survey</h1>
          <p className="text-gray-600">
            Project: {survey.project_name} | Role: {role}
          </p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Question {currentQuestion + 1} of {survey.questions.length}</span>
            <span>{Math.round(progress)}% Complete</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <motion.div 
              className="bg-pink-500 h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>

        {/* Question Card */}
        <motion.div 
          key={currentQuestion}
          className="bg-white rounded-lg shadow-lg p-8 mb-8"
          initial={{ x: 50, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <h2 className="text-xl font-semibold text-gray-900 mb-6">
            {question.question_text}
          </h2>

          {question.question_type === 'scale' && (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map(value => (
                <label key={value} className="flex items-center cursor-pointer">
                  <input
                    type="radio"
                    name={`question_${question.id}`}
                    value={value}
                    checked={responses[question.id] === value}
                    onChange={() => handleResponse(question.id, value)}
                    className="mr-3 text-pink-500"
                  />
                  <span className="text-gray-700">
                    {value} - {value === 1 ? 'Strongly Disagree' : 
                          value === 2 ? 'Disagree' : 
                          value === 3 ? 'Neutral' : 
                          value === 4 ? 'Agree' : 'Strongly Agree'}
                  </span>
                </label>
              ))}
            </div>
          )}

          {question.question_type === 'text' && (
            <textarea
              className="w-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
              rows="4"
              placeholder="Please share your thoughts..."
              value={responses[question.id] || ''}
              onChange={(e) => handleResponse(question.id, e.target.value)}
            />
          )}

          {question.question_type === 'multiple_choice' && question.options && (
            <div className="space-y-3">
              {question.options.map((option, index) => (
                <label key={index} className="flex items-center cursor-pointer">
                  <input
                    type="radio"
                    name={`question_${question.id}`}
                    value={option}
                    checked={responses[question.id] === option}
                    onChange={() => handleResponse(question.id, option)}
                    className="mr-3 text-pink-500"
                  />
                  <span className="text-gray-700">{option}</span>
                </label>
              ))}
            </div>
          )}
        </motion.div>

        {/* Navigation */}
        <div className="flex justify-between">
          <button
            onClick={() => setCurrentQuestion(Math.max(0, currentQuestion - 1))}
            disabled={currentQuestion === 0}
            className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg font-medium disabled:opacity-50 hover:bg-gray-300 transition-colors"
          >
            Previous
          </button>

          {currentQuestion < survey.questions.length - 1 ? (
            <button
              onClick={() => setCurrentQuestion(currentQuestion + 1)}
              disabled={!responses[question.id]}
              className="px-6 py-3 bg-pink-500 text-white rounded-lg font-medium disabled:opacity-50 hover:bg-pink-600 transition-colors"
            >
              Next
            </button>
          ) : (
            <button
              onClick={submitSurvey}
              disabled={!responses[question.id] || submitting}
              className="px-6 py-3 bg-green-500 text-white rounded-lg font-medium disabled:opacity-50 hover:bg-green-600 transition-colors"
            >
              {submitting ? 'Submitting...' : 'Submit Survey'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Survey;