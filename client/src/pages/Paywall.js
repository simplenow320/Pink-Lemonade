import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Paywall = () => {
  const [selectedPlan, setSelectedPlan] = useState('professional');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { user } = useAuth();

  const plans = [
    {
      id: 'starter',
      name: 'Starter',
      price: '$29',
      period: '/month',
      description: 'Perfect for small nonprofits getting started',
      features: [
        'Up to 10 grant applications per month',
        'Basic AI writing assistance',
        'Grant discovery and matching',
        'Email support',
        'Basic analytics dashboard'
      ],
      highlighted: false
    },
    {
      id: 'professional',
      name: 'Professional',
      price: '$79',
      period: '/month',
      description: 'Most popular for growing organizations',
      features: [
        'Unlimited grant applications',
        'Advanced AI Smart Tools suite',
        'Premium grant matching',
        'Priority email & phone support',
        'Advanced analytics & reporting',
        'Organization profile optimization',
        'Grant deadline reminders',
        'Export capabilities'
      ],
      highlighted: true
    },
    {
      id: 'enterprise',
      name: 'Enterprise',
      price: '$199',
      period: '/month',
      description: 'For large organizations with complex needs',
      features: [
        'Everything in Professional',
        'Multi-user team access',
        'Custom AI training',
        'Dedicated account manager',
        'Custom integrations',
        'Advanced compliance features',
        'White-label options',
        'Custom reporting'
      ],
      highlighted: false
    }
  ];

  const handleUpgrade = async (planId) => {
    setLoading(true);
    
    try {
      // For demo purposes, we'll simulate a successful upgrade
      // In a real app, this would integrate with Stripe or another payment processor
      
      // Simulate payment processing
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // For now, just redirect to dashboard
      // In production, this would handle actual payment processing
      alert(`Upgrade to ${plans.find(p => p.id === planId)?.name} plan would be processed here. For demo purposes, proceeding to dashboard.`);
      
      navigate('/dashboard');
    } catch (error) {
      console.error('Upgrade failed:', error);
      alert('Upgrade failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleFreeTrial = () => {
    // For demo purposes, allow access to dashboard
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-white py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <motion.div 
          className="text-center mb-12"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Unlock the Full Power of Pink Lemonade
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Your organization profile is complete! Now choose the plan that fits your grant management needs.
          </p>
        </motion.div>

        {/* User Welcome */}
        {user && (
          <motion.div 
            className="bg-white rounded-lg shadow-md p-6 mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Welcome, {user.first_name}!
                </h3>
                <p className="text-gray-600">
                  Your profile is set up for {user.org_name}. Ready to find the perfect grants?
                </p>
              </div>
              <div className="flex-shrink-0">
                <div className="bg-green-100 rounded-full p-3">
                  <svg className="w-6 h-6 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Free Trial Banner */}
        <motion.div 
          className="bg-gradient-to-r from-blue-50 to-blue-100 border border-blue-200 rounded-lg p-6 mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-blue-900 mb-2">
                Start Your 14-Day Free Trial
              </h3>
              <p className="text-blue-700">
                Test all Professional features at no cost. No credit card required.
              </p>
            </div>
            <button
              onClick={handleFreeTrial}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
            >
              Start Free Trial
            </button>
          </div>
        </motion.div>

        {/* Pricing Plans */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((plan, index) => (
            <motion.div
              key={plan.id}
              className={`bg-white rounded-xl shadow-lg overflow-hidden ${
                plan.highlighted ? 'ring-2 ring-pink-500 ring-offset-2' : ''
              }`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 + index * 0.1 }}
            >
              {plan.highlighted && (
                <div className="bg-gradient-to-r from-pink-500 to-pink-600 text-white text-center py-2 text-sm font-medium">
                  Most Popular
                </div>
              )}
              
              <div className="p-8">
                <div className="text-center mb-6">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                  <div className="flex items-baseline justify-center">
                    <span className="text-4xl font-bold text-gray-900">{plan.price}</span>
                    <span className="text-gray-500 ml-1">{plan.period}</span>
                  </div>
                  <p className="text-gray-600 mt-2">{plan.description}</p>
                </div>

                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start">
                      <svg className="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      <span className="text-gray-700 text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => handleUpgrade(plan.id)}
                  disabled={loading}
                  className={`w-full py-3 px-4 rounded-lg font-medium transition-all ${
                    plan.highlighted
                      ? 'bg-gradient-to-r from-pink-500 to-pink-600 text-white hover:from-pink-600 hover:to-pink-700'
                      : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                  } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {loading ? 'Processing...' : `Choose ${plan.name}`}
                </button>
              </div>
            </motion.div>
          ))}
        </div>

        {/* FAQ Section */}
        <motion.div 
          className="mt-16 text-center"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.8 }}
        >
          <h2 className="text-2xl font-bold text-gray-900 mb-8">Frequently Asked Questions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-left">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Can I change plans later?</h3>
              <p className="text-gray-600">Yes, you can upgrade or downgrade your plan at any time. Changes take effect immediately.</p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Is there a setup fee?</h3>
              <p className="text-gray-600">No setup fees. All plans include free onboarding and setup assistance.</p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">What payment methods do you accept?</h3>
              <p className="text-gray-600">We accept all major credit cards and ACH bank transfers for annual plans.</p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Can I cancel anytime?</h3>
              <p className="text-gray-600">Yes, cancel anytime with no penalties. You'll retain access through your billing period.</p>
            </div>
          </div>
        </motion.div>

        {/* Support Contact */}
        <motion.div 
          className="mt-12 text-center"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 1.0 }}
        >
          <p className="text-gray-600">
            Need help choosing the right plan?{' '}
            <a href="mailto:support@pinklemonade.com" className="text-pink-600 hover:text-pink-500 font-medium">
              Contact our team
            </a>
          </p>
        </motion.div>
      </div>
    </div>
  );
};

export default Paywall;