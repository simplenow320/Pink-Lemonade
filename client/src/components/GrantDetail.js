import React, { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { getGrant, updateGrant, deleteGrant, matchGrant } from '../utils/api';
import { formatCurrency, formatDate, getDateUrgencyClass, formatMatchScore, getStatusClass } from '../utils/formatters';

const GrantDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [grant, setGrant] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({});
  const [matchLoading, setMatchLoading] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  
  // Status options for dropdown
  const statusOptions = [
    'Not Started', 
    'In Progress', 
    'Submitted', 
    'Won', 
    'Declined'
  ];
  
  // Load grant data
  useEffect(() => {
    const fetchGrantData = async () => {
      setLoading(true);
      try {
        const data = await getGrant(id);
        setGrant(data);
        // Initialize edit form with current values
        setEditForm({
          title: data.title || '',
          funder: data.funder || '',
          description: data.description || '',
          amount: data.amount || '',
          due_date: data.due_date ? data.due_date.substring(0, 10) : '', // Format for date input
          eligibility: data.eligibility || '',
          website: data.website || '',
          status: data.status || 'Not Started',
          notes: data.notes || '',
          focus_areas: data.focus_areas ? data.focus_areas.join(', ') : '',
          contact_info: data.contact_info || ''
        });
        setError(null);
      } catch (err) {
        console.error('Error fetching grant:', err);
        setError('Failed to load grant details. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchGrantData();
  }, [id]);
  
  // Handle form changes
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setEditForm({
      ...editForm,
      [name]: value
    });
  };
  
  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Process focus areas from comma-separated string to array
    const formData = {
      ...editForm,
      focus_areas: editForm.focus_areas
        ? editForm.focus_areas.split(',').map(area => area.trim())
        : []
    };
    
    try {
      const updatedGrant = await updateGrant(id, formData);
      setGrant(updatedGrant);
      setIsEditing(false);
      alert('Grant updated successfully');
    } catch (err) {
      console.error('Error updating grant:', err);
      alert('Failed to update grant. Please try again.');
    }
  };
  
  // Handle delete grant
  const handleDelete = async () => {
    try {
      await deleteGrant(id);
      navigate('/grants');
      alert('Grant deleted successfully');
    } catch (err) {
      console.error('Error deleting grant:', err);
      alert('Failed to delete grant. Please try again.');
    }
  };
  
  // Handle match calculation
  const handleMatchCalculation = async () => {
    setMatchLoading(true);
    try {
      const matchResult = await matchGrant(id);
      setGrant({
        ...grant,
        match_score: matchResult.score,
        match_explanation: matchResult.explanation
      });
    } catch (err) {
      console.error('Error calculating match:', err);
      alert('Failed to calculate match score. Please try again.');
    } finally {
      setMatchLoading(false);
    }
  };
  
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }
  
  if (!grant) {
    return (
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-yellow-700">Grant not found</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-bold text-gray-900">{grant.title}</h1>
          <p className="mt-1 text-sm text-gray-500">
            From <span className="font-medium">{grant.funder}</span>
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4 space-x-3">
          <Link
            to={`/narratives/${grant.id}`}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
          >
            <svg className="-ml-1 mr-2 h-5 w-5 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Generate Narrative
          </Link>
          {isEditing ? (
            <button
              type="button"
              onClick={() => setIsEditing(false)}
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
            >
              Cancel Editing
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setIsEditing(true)}
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
            >
              <svg className="-ml-1 mr-2 h-5 w-5 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
              Edit Grant
            </button>
          )}
          <button
            type="button"
            onClick={() => setDeleteModalOpen(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
          >
            <svg className="-ml-1 mr-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            Delete
          </button>
        </div>
      </div>
      
      {/* Grant Details */}
      {isEditing ? (
        <div className="bg-white shadow overflow-hidden rounded-lg">
          <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Edit Grant Details
            </h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              Update information about this grant opportunity
            </p>
          </div>
          <div className="px-4 py-5 sm:p-6">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="title" className="block text-sm font-medium text-gray-700">Title</label>
                  <input
                    type="text"
                    name="title"
                    id="title"
                    className="mt-1 focus:ring-primary focus:border-primary block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                    value={editForm.title}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div>
                  <label htmlFor="funder" className="block text-sm font-medium text-gray-700">Funder</label>
                  <input
                    type="text"
                    name="funder"
                    id="funder"
                    className="mt-1 focus:ring-primary focus:border-primary block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                    value={editForm.funder}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                <div>
                  <label htmlFor="amount" className="block text-sm font-medium text-gray-700">Amount</label>
                  <div className="mt-1 relative rounded-md shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <span className="text-gray-500 sm:text-sm">$</span>
                    </div>
                    <input
                      type="number"
                      name="amount"
                      id="amount"
                      className="focus:ring-primary focus:border-primary block w-full pl-7 sm:text-sm border-gray-300 rounded-md"
                      value={editForm.amount}
                      onChange={handleInputChange}
                    />
                  </div>
                </div>
                <div>
                  <label htmlFor="due_date" className="block text-sm font-medium text-gray-700">Due Date</label>
                  <input
                    type="date"
                    name="due_date"
                    id="due_date"
                    className="mt-1 focus:ring-primary focus:border-primary block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                    value={editForm.due_date}
                    onChange={handleInputChange}
                  />
                </div>
                <div>
                  <label htmlFor="status" className="block text-sm font-medium text-gray-700">Status</label>
                  <select
                    id="status"
                    name="status"
                    className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary focus:border-primary sm:text-sm rounded-md"
                    value={editForm.status}
                    onChange={handleInputChange}
                  >
                    {statusOptions.map(option => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor="website" className="block text-sm font-medium text-gray-700">Website</label>
                  <input
                    type="url"
                    name="website"
                    id="website"
                    className="mt-1 focus:ring-primary focus:border-primary block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                    value={editForm.website}
                    onChange={handleInputChange}
                  />
                </div>
                <div className="md:col-span-2">
                  <label htmlFor="description" className="block text-sm font-medium text-gray-700">Description</label>
                  <textarea
                    id="description"
                    name="description"
                    rows={3}
                    className="mt-1 shadow-sm focus:ring-primary focus:border-primary block w-full sm:text-sm border-gray-300 rounded-md"
                    value={editForm.description}
                    onChange={handleInputChange}
                  />
                </div>
                <div className="md:col-span-2">
                  <label htmlFor="eligibility" className="block text-sm font-medium text-gray-700">Eligibility</label>
                  <textarea
                    id="eligibility"
                    name="eligibility"
                    rows={3}
                    className="mt-1 shadow-sm focus:ring-primary focus:border-primary block w-full sm:text-sm border-gray-300 rounded-md"
                    value={editForm.eligibility}
                    onChange={handleInputChange}
                  />
                </div>
                <div>
                  <label htmlFor="focus_areas" className="block text-sm font-medium text-gray-700">Focus Areas</label>
                  <input
                    type="text"
                    name="focus_areas"
                    id="focus_areas"
                    className="mt-1 focus:ring-primary focus:border-primary block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                    value={editForm.focus_areas}
                    onChange={handleInputChange}
                    placeholder="Comma-separated list"
                  />
                </div>
                <div>
                  <label htmlFor="contact_info" className="block text-sm font-medium text-gray-700">Contact Information</label>
                  <input
                    type="text"
                    name="contact_info"
                    id="contact_info"
                    className="mt-1 focus:ring-primary focus:border-primary block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                    value={editForm.contact_info}
                    onChange={handleInputChange}
                  />
                </div>
                <div className="md:col-span-2">
                  <label htmlFor="notes" className="block text-sm font-medium text-gray-700">Notes</label>
                  <textarea
                    id="notes"
                    name="notes"
                    rows={3}
                    className="mt-1 shadow-sm focus:ring-primary focus:border-primary block w-full sm:text-sm border-gray-300 rounded-md"
                    value={editForm.notes}
                    onChange={handleInputChange}
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Left column - Main details */}
          <div className="md:col-span-2 space-y-6">
            <div className="bg-white shadow overflow-hidden rounded-lg">
              <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Grant Details
                </h3>
                <p className="mt-1 max-w-2xl text-sm text-gray-500">
                  {grant.is_scraped && (
                    <span className="inline-flex items-center">
                      <svg className="mr-1.5 h-4 w-4 text-green-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                      </svg>
                      Automatically discovered via scraper
                    </span>
                  )}
                </p>
              </div>
              <div className="px-4 py-5 sm:p-6">
                <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-6">
                  <div className="sm:col-span-1">
                    <dt className="text-sm font-medium text-gray-500">Funder</dt>
                    <dd className="mt-1 text-sm text-gray-900">{grant.funder}</dd>
                  </div>
                  <div className="sm:col-span-1">
                    <dt className="text-sm font-medium text-gray-500">Amount</dt>
                    <dd className="mt-1 text-sm text-gray-900">{formatCurrency(grant.amount)}</dd>
                  </div>
                  <div className="sm:col-span-1">
                    <dt className="text-sm font-medium text-gray-500">Due Date</dt>
                    <dd className={`mt-1 text-sm ${getDateUrgencyClass(grant.due_date)}`}>
                      {formatDate(grant.due_date)}
                    </dd>
                  </div>
                  <div className="sm:col-span-1">
                    <dt className="text-sm font-medium text-gray-500">Status</dt>
                    <dd className="mt-1 text-sm">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusClass(grant.status)}`}>
                        {grant.status}
                      </span>
                    </dd>
                  </div>
                  <div className="sm:col-span-2">
                    <dt className="text-sm font-medium text-gray-500">Description</dt>
                    <dd className="mt-1 text-sm text-gray-900 whitespace-pre-line">
                      {grant.description || 'No description available'}
                    </dd>
                  </div>
                  <div className="sm:col-span-2">
                    <dt className="text-sm font-medium text-gray-500">Eligibility</dt>
                    <dd className="mt-1 text-sm text-gray-900 whitespace-pre-line">
                      {grant.eligibility || 'No eligibility information available'}
                    </dd>
                  </div>
                  <div className="sm:col-span-1">
                    <dt className="text-sm font-medium text-gray-500">Website</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {grant.website ? (
                        <a 
                          href={grant.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:text-primary-dark hover:underline"
                        >
                          Visit grant website
                        </a>
                      ) : (
                        'No website available'
                      )}
                    </dd>
                  </div>
                  <div className="sm:col-span-1">
                    <dt className="text-sm font-medium text-gray-500">Contact Information</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {grant.contact_info || 'No contact information available'}
                    </dd>
                  </div>
                  <div className="sm:col-span-2">
                    <dt className="text-sm font-medium text-gray-500">Focus Areas</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {grant.focus_areas && grant.focus_areas.length > 0 ? (
                        <div className="flex flex-wrap gap-2">
                          {grant.focus_areas.map((area, index) => (
                            <span 
                              key={index}
                              className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-light text-primary"
                            >
                              {area}
                            </span>
                          ))}
                        </div>
                      ) : (
                        'No focus areas specified'
                      )}
                    </dd>
                  </div>
                  <div className="sm:col-span-2">
                    <dt className="text-sm font-medium text-gray-500">Notes</dt>
                    <dd className="mt-1 text-sm text-gray-900 whitespace-pre-line">
                      {grant.notes || 'No notes available'}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>
          </div>
          
          {/* Right column - Match score and other metadata */}
          <div className="md:col-span-1 space-y-6">
            <div className="bg-white shadow overflow-hidden rounded-lg">
              <div className="px-4 py-5 sm:px-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Organization Match
                </h3>
              </div>
              <div className="px-4 py-5 sm:p-6">
                <div className="mb-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-500">Match Score</span>
                    <span className={`text-sm font-medium ${getMatchScoreClass(grant.match_score)}`}>
                      {formatMatchScore(grant.match_score)}
                    </span>
                  </div>
                  <div className="mt-2 w-full bg-gray-200 rounded-full h-2.5">
                    <div 
                      className="bg-primary h-2.5 rounded-full" 
                      style={{ width: `${grant.match_score || 0}%` }}
                    ></div>
                  </div>
                </div>
                
                <div className="mt-6">
                  <h4 className="text-sm font-medium text-gray-500 mb-2">Match Analysis</h4>
                  <p className="text-sm text-gray-700 whitespace-pre-line">
                    {grant.match_explanation || 'No match analysis available. Click "Calculate Match" to analyze this grant against your organization profile.'}
                  </p>
                </div>
                
                <div className="mt-6">
                  <button
                    type="button"
                    onClick={handleMatchCalculation}
                    disabled={matchLoading}
                    className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50"
                  >
                    {matchLoading ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Calculating...
                      </>
                    ) : (
                      <>
                        <svg className="-ml-1 mr-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                        </svg>
                        Calculate Match
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
            
            <div className="bg-white shadow overflow-hidden rounded-lg">
              <div className="px-4 py-5 sm:px-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Grant Timeline
                </h3>
              </div>
              <div className="px-4 py-5 sm:p-6">
                <ol className="border-l-2 border-primary">
                  <li className="ml-6 mb-6">
                    <span className="absolute flex items-center justify-center bg-primary text-white rounded-full h-6 w-6 -ml-10">
                      <svg className="h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                      </svg>
                    </span>
                    <h4 className="text-sm font-semibold">Created</h4>
                    <p className="text-xs text-gray-500">{formatDate(grant.created_at)}</p>
                  </li>
                  
                  <li className="ml-6 mb-6">
                    <span className={`absolute flex items-center justify-center ${grant.status === 'Not Started' ? 'bg-primary' : 'bg-gray-200'} text-white rounded-full h-6 w-6 -ml-10`}>
                      <svg className="h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                      </svg>
                    </span>
                    <h4 className="text-sm font-semibold">Application Started</h4>
                    <p className="text-xs text-gray-500">Not yet started</p>
                  </li>
                  
                  <li className="ml-6 mb-6">
                    <span className={`absolute flex items-center justify-center ${grant.status === 'Submitted' ? 'bg-primary' : 'bg-gray-200'} text-white rounded-full h-6 w-6 -ml-10`}>
                      <svg className="h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </span>
                    <h4 className="text-sm font-semibold">Submitted</h4>
                    <p className="text-xs text-gray-500">Not yet submitted</p>
                  </li>
                  
                  <li className="ml-6">
                    <span className={`absolute flex items-center justify-center ${grant.status === 'Won' || grant.status === 'Declined' ? 'bg-primary' : 'bg-gray-200'} text-white rounded-full h-6 w-6 -ml-10`}>
                      <svg className="h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9" />
                      </svg>
                    </span>
                    <h4 className="text-sm font-semibold">Decision</h4>
                    <p className="text-xs text-gray-500">
                      {grant.status === 'Won' ? 'Awarded' : grant.status === 'Declined' ? 'Declined' : 'Pending'}
                    </p>
                  </li>
                </ol>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Delete Confirmation Modal */}
      {deleteModalOpen && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10">
                    <svg className="h-6 w-6 text-red-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      Delete Grant
                    </h3>
                    <div className="mt-2">
                      <p className="text-sm text-gray-500">
                        Are you sure you want to delete this grant? This action cannot be undone.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  onClick={handleDelete}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Delete
                </button>
                <button
                  type="button"
                  onClick={() => setDeleteModalOpen(false)}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GrantDetail;
