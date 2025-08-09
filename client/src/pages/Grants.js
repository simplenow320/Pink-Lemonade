import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useGrants } from '../hooks/useGrants';
import { formatCurrency, formatDate, getDateUrgencyClass, getStatusClass, formatMatchScore } from '../utils/formatters';
import { motion } from 'framer-motion';

const Grants = () => {
  const navigate = useNavigate();
  const { grants, loading, error, refreshData } = useGrants();
  const [filteredGrants, setFilteredGrants] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [sortBy, setSortBy] = useState('due_date');
  const [sortDirection, setSortDirection] = useState('asc');
  
  // Status options for filtering
  const statusOptions = ['All', 'Not Started', 'In Progress', 'Submitted', 'Won', 'Declined'];
  
  // Effect to filter and sort grants
  useEffect(() => {
    if (grants) {
      let filtered = [...grants];
      
      // Apply status filter
      if (statusFilter !== 'All') {
        filtered = filtered.filter(grant => grant.status === statusFilter);
      }
      
      // Apply search filter
      if (searchTerm.trim() !== '') {
        const term = searchTerm.toLowerCase();
        filtered = filtered.filter(grant => 
          grant.title.toLowerCase().includes(term) || 
          grant.funder.toLowerCase().includes(term) || 
          (grant.description && grant.description.toLowerCase().includes(term))
        );
      }
      
      // Apply sorting
      filtered.sort((a, b) => {
        // Handle empty values
        if (!a[sortBy] && !b[sortBy]) return 0;
        if (!a[sortBy]) return 1;
        if (!b[sortBy]) return -1;
        
        // Special case for dates
        if (sortBy === 'due_date') {
          const dateA = new Date(a.due_date || '9999-12-31');
          const dateB = new Date(b.due_date || '9999-12-31');
          return sortDirection === 'asc' ? dateA - dateB : dateB - dateA;
        }
        
        // Handle numeric values
        if (typeof a[sortBy] === 'number') {
          return sortDirection === 'asc' ? a[sortBy] - b[sortBy] : b[sortBy] - a[sortBy];
        }
        
        // Handle string values
        const valueA = String(a[sortBy]).toLowerCase();
        const valueB = String(b[sortBy]).toLowerCase();
        return sortDirection === 'asc' 
          ? valueA.localeCompare(valueB) 
          : valueB.localeCompare(valueA);
      });
      
      setFilteredGrants(filtered);
    }
  }, [grants, statusFilter, searchTerm, sortBy, sortDirection]);
  
  // Function to toggle sort direction
  const handleSort = (field) => {
    if (sortBy === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortDirection('asc');
    }
  };
  
  const renderSortIcon = (field) => {
    if (sortBy !== field) return null;
    
    return sortDirection === 'asc' ? (
      <svg className="ml-1 w-4 h-4 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 15l7-7 7 7" />
      </svg>
    ) : (
      <svg className="ml-1 w-4 h-4 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
      </svg>
    );
  };
  
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-orange-500"></div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded-md">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
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

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row justify-between md:items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Grants</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage and track all your grant opportunities
          </p>
        </div>
        <div className="mt-4 md:mt-0">
          <Link
            to="/grants/add"
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-orange-600 hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500"
          >
            <svg className="-ml-1 mr-2 h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clipRule="evenodd" />
            </svg>
            Add New Grant
          </Link>
        </div>
      </div>
      
      {/* Filters and search */}
      <div className="bg-white rounded-lg shadow-sm p-4">
        <div className="flex flex-col md:flex-row space-y-4 md:space-y-0 md:space-x-4">
          <div className="flex-1">
            <label htmlFor="search" className="sr-only">Search</label>
            <div className="relative rounded-md shadow-sm">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                </svg>
              </div>
              <input
                type="text"
                name="search"
                id="search"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="focus:ring-orange-500 focus:border-orange-500 block w-full pl-10 sm:text-sm border-gray-300 rounded-md py-2"
                placeholder="Search grants..."
              />
            </div>
          </div>
          <div className="w-full md:w-48">
            <label htmlFor="status" className="sr-only">Status</label>
            <select
              id="status"
              name="status"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="focus:ring-orange-500 focus:border-orange-500 block w-full py-2 pl-3 pr-10 text-base border-gray-300 rounded-md"
            >
              {statusOptions.map(option => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          </div>
          <div className="w-full md:w-48">
            <label htmlFor="sort" className="sr-only">Sort By</label>
            <select
              id="sort"
              name="sort"
              value={sortBy}
              onChange={(e) => {
                setSortBy(e.target.value);
                setSortDirection('asc');
              }}
              className="focus:ring-orange-500 focus:border-orange-500 block w-full py-2 pl-3 pr-10 text-base border-gray-300 rounded-md"
            >
              <option value="due_date">Due Date</option>
              <option value="title">Title</option>
              <option value="funder">Funder</option>
              <option value="amount">Amount</option>
              <option value="match_score">Match Score</option>
            </select>
          </div>
          <div className="w-full md:w-48">
            <label htmlFor="direction" className="sr-only">Direction</label>
            <select
              id="direction"
              name="direction"
              value={sortDirection}
              onChange={(e) => setSortDirection(e.target.value)}
              className="focus:ring-orange-500 focus:border-orange-500 block w-full py-2 pl-3 pr-10 text-base border-gray-300 rounded-md"
            >
              <option value="asc">Ascending</option>
              <option value="desc">Descending</option>
            </select>
          </div>
        </div>
      </div>
      
      {/* Grants list */}
      <div className="bg-white shadow-sm rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th 
                  scope="col" 
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                  onClick={() => handleSort('title')}
                >
                  <div className="flex items-center">
                    Title {renderSortIcon('title')}
                  </div>
                </th>
                <th 
                  scope="col" 
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                  onClick={() => handleSort('funder')}
                >
                  <div className="flex items-center">
                    Funder {renderSortIcon('funder')}
                  </div>
                </th>
                <th 
                  scope="col" 
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                  onClick={() => handleSort('amount')}
                >
                  <div className="flex items-center">
                    Amount {renderSortIcon('amount')}
                  </div>
                </th>
                <th 
                  scope="col" 
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                  onClick={() => handleSort('due_date')}
                >
                  <div className="flex items-center">
                    Due Date {renderSortIcon('due_date')}
                  </div>
                </th>
                <th 
                  scope="col" 
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                  onClick={() => handleSort('match_score')}
                >
                  <div className="flex items-center">
                    Match {renderSortIcon('match_score')}
                  </div>
                </th>
                <th 
                  scope="col" 
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                  onClick={() => handleSort('status')}
                >
                  <div className="flex items-center">
                    Status {renderSortIcon('status')}
                  </div>
                </th>
                <th scope="col" className="relative px-6 py-3">
                  <span className="sr-only">View</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredGrants.length > 0 ? (
                filteredGrants.map((grant) => (
                  <motion.tr 
                    key={grant.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.3 }}
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => navigate(`/grants/${grant.id}`)}
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link to={`/grants/${grant.id}`} className="text-sm font-medium text-gray-900 hover:text-orange-600 hover:underline">
                        {grant.title}
                      </Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">{grant.funder}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">
                        {grant.amount ? formatCurrency(grant.amount) : '-'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`text-sm ${getDateUrgencyClass(grant.due_date)}`}>
                        {grant.due_date ? formatDate(grant.due_date) : 'No deadline'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {formatMatchScore(grant.match_score)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusClass(grant.status)}`}>
                        {grant.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <Link to={`/grants/${grant.id}`} className="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-orange-600 hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500">
                        View Details
                      </Link>
                    </td>
                  </motion.tr>
                ))
              ) : (
                <tr>
                  <td colSpan="7" className="px-6 py-10 text-center text-gray-500">
                    <div className="flex flex-col items-center">
                      <svg className="w-12 h-12 text-gray-400 mb-3" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <p className="text-base">No grants found matching your criteria</p>
                      <button 
                        onClick={() => {
                          setSearchTerm('');
                          setStatusFilter('All');
                          setSortBy('due_date');
                          setSortDirection('asc');
                        }}
                        className="mt-3 text-sm text-orange-600 hover:text-orange-500 font-medium"
                      >
                        Clear filters
                      </button>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Grants;