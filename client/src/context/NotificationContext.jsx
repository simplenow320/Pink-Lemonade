import React, { createContext, useContext, useState, useCallback } from 'react';
import PropTypes from 'prop-types';

// Create the notification context
const NotificationContext = createContext();

// Notification types
export const NOTIFICATION_TYPES = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info',
};

/**
 * Provider component for notifications
 */
export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);

  // Add a new notification
  const addNotification = useCallback(
    (message, type = NOTIFICATION_TYPES.INFO, duration = 5000) => {
      const id = Date.now() + Math.random().toString(36).substring(2, 9);
      const newNotification = { id, message, type, duration };

      setNotifications((prevNotifications) => [...prevNotifications, newNotification]);

      // Auto-remove the notification after duration
      if (duration > 0) {
        setTimeout(() => {
          removeNotification(id);
        }, duration);
      }

      return id;
    },
    []
  );

  // Add specific notification types
  const addSuccess = useCallback(
    (message, duration) => addNotification(message, NOTIFICATION_TYPES.SUCCESS, duration),
    [addNotification]
  );

  const addError = useCallback(
    (message, duration) => addNotification(message, NOTIFICATION_TYPES.ERROR, duration),
    [addNotification]
  );

  const addWarning = useCallback(
    (message, duration) => addNotification(message, NOTIFICATION_TYPES.WARNING, duration),
    [addNotification]
  );

  const addInfo = useCallback(
    (message, duration) => addNotification(message, NOTIFICATION_TYPES.INFO, duration),
    [addNotification]
  );

  // Remove a notification by id
  const removeNotification = useCallback((id) => {
    setNotifications((prevNotifications) =>
      prevNotifications.filter((notification) => notification.id !== id)
    );
  }, []);

  // Clear all notifications
  const clearAllNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  const value = {
    notifications,
    addNotification,
    addSuccess,
    addError,
    addWarning,
    addInfo,
    removeNotification,
    clearAllNotifications,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
      <NotificationDisplay notifications={notifications} removeNotification={removeNotification} />
    </NotificationContext.Provider>
  );
};

NotificationProvider.propTypes = {
  children: PropTypes.node.isRequired,
};

/**
 * Component to display notifications
 */
const NotificationDisplay = ({ notifications, removeNotification }) => {
  if (notifications.length === 0) return null;

  return (
    <div className="notification-container fixed bottom-0 right-0 p-4 z-50 space-y-2 max-w-md">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`notification rounded-lg shadow-lg p-4 flex justify-between items-start
            ${notification.type === NOTIFICATION_TYPES.SUCCESS ? 'bg-green-100 border-l-4 border-green-500 text-green-700' : ''}
            ${notification.type === NOTIFICATION_TYPES.ERROR ? 'bg-red-100 border-l-4 border-red-500 text-red-700' : ''}
            ${notification.type === NOTIFICATION_TYPES.WARNING ? 'bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700' : ''}
            ${notification.type === NOTIFICATION_TYPES.INFO ? 'bg-blue-100 border-l-4 border-blue-500 text-blue-700' : ''}
          `}
        >
          <div className="mr-3 flex-grow">
            <p className="break-words">{notification.message}</p>
          </div>
          <button
            onClick={() => removeNotification(notification.id)}
            className="text-gray-500 hover:text-gray-700 focus:outline-none"
            aria-label="Close notification"
          >
            &times;
          </button>
        </div>
      ))}
    </div>
  );
};

NotificationDisplay.propTypes = {
  notifications: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      message: PropTypes.string.isRequired,
      type: PropTypes.oneOf(Object.values(NOTIFICATION_TYPES)).isRequired,
    })
  ).isRequired,
  removeNotification: PropTypes.func.isRequired,
};

/**
 * Custom hook to use notifications
 */
export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};

export default NotificationContext;
