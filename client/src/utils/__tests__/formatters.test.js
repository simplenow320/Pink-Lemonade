import {
  formatDate,
  formatDateTime,
  formatCurrency,
  getStatusClass,
  getDateUrgencyClass,
  getMatchScoreClass,
  formatMatchScore,
  truncateText,
  formatDuration
} from '../formatters';

// Mock Date to ensure consistent results in tests
const mockDate = new Date('2025-05-09T12:00:00Z');
const realDate = global.Date;

// Setup and teardown for Date mocking
beforeEach(() => {
  global.Date = class extends Date {
    constructor(date) {
      if (date) {
        return new realDate(date);
      }
      return mockDate;
    }
  };
});

afterEach(() => {
  global.Date = realDate;
});

describe('formatDate', () => {
  test('formats a date string correctly', () => {
    expect(formatDate('2025-01-15')).toBe('Jan 15, 2025');
  });

  test('returns N/A for null or undefined', () => {
    expect(formatDate(null)).toBe('N/A');
    expect(formatDate(undefined)).toBe('N/A');
    expect(formatDate('')).toBe('N/A');
  });
});

describe('formatDateTime', () => {
  test('formats a datetime string correctly including time', () => {
    expect(formatDateTime('2025-01-15T14:30:00')).toMatch(/Jan 15, 2025.*(2|02):30/);
  });

  test('returns N/A for null or undefined', () => {
    expect(formatDateTime(null)).toBe('N/A');
    expect(formatDateTime(undefined)).toBe('N/A');
  });
});

describe('formatCurrency', () => {
  test('formats currency with dollar sign and no decimals', () => {
    expect(formatCurrency(1000)).toBe('$1,000');
    expect(formatCurrency(1000.50)).toBe('$1,001'); // Rounds
  });

  test('returns N/A for null or undefined', () => {
    expect(formatCurrency(null)).toBe('N/A');
    expect(formatCurrency(undefined)).toBe('N/A');
  });
});

describe('getStatusClass', () => {
  test('returns appropriate class based on status', () => {
    expect(getStatusClass('Not Started')).toBe('bg-gray-200 text-gray-700');
    expect(getStatusClass('In Progress')).toBe('bg-blue-100 text-blue-800');
    expect(getStatusClass('Submitted')).toBe('bg-yellow-100 text-yellow-800');
    expect(getStatusClass('Won')).toBe('bg-green-100 text-green-800');
    expect(getStatusClass('Declined')).toBe('bg-red-100 text-red-800');
  });

  test('returns default class for unknown status', () => {
    expect(getStatusClass('Unknown Status')).toBe('bg-gray-100 text-gray-800');
  });

  test('returns empty string for null or undefined', () => {
    expect(getStatusClass(null)).toBe('');
    expect(getStatusClass(undefined)).toBe('');
  });
});

describe('getDateUrgencyClass', () => {
  test('returns red class for past dates', () => {
    const pastDate = new Date();
    pastDate.setDate(pastDate.getDate() - 5);
    expect(getDateUrgencyClass(pastDate.toISOString())).toBe('text-red-600 font-medium');
  });

  test('returns yellow class for dates within 14 days', () => {
    const soonDate = new Date();
    soonDate.setDate(soonDate.getDate() + 7);
    expect(getDateUrgencyClass(soonDate.toISOString())).toBe('text-yellow-600 font-medium');
  });

  test('returns blue class for dates more than 14 days away', () => {
    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + 30);
    expect(getDateUrgencyClass(futureDate.toISOString())).toBe('text-blue-600');
  });

  test('returns empty string for null or undefined', () => {
    expect(getDateUrgencyClass(null)).toBe('');
    expect(getDateUrgencyClass(undefined)).toBe('');
  });
});

describe('getMatchScoreClass', () => {
  test('returns green class for scores >= 80', () => {
    expect(getMatchScoreClass(80)).toBe('text-green-600 font-medium');
    expect(getMatchScoreClass(95)).toBe('text-green-600 font-medium');
  });

  test('returns yellow class for scores >= 50 and < 80', () => {
    expect(getMatchScoreClass(50)).toBe('text-yellow-600 font-medium');
    expect(getMatchScoreClass(79)).toBe('text-yellow-600 font-medium');
  });

  test('returns gray class for scores < 50', () => {
    expect(getMatchScoreClass(49)).toBe('text-gray-600');
    expect(getMatchScoreClass(10)).toBe('text-gray-600');
  });

  test('returns empty string for null or undefined', () => {
    expect(getMatchScoreClass(null)).toBe('');
    expect(getMatchScoreClass(undefined)).toBe('');
  });
});

describe('formatMatchScore', () => {
  test('formats score as percentage', () => {
    expect(formatMatchScore(75.5)).toBe('76%');
    expect(formatMatchScore(30)).toBe('30%');
  });

  test('returns N/A for null or undefined', () => {
    expect(formatMatchScore(null)).toBe('N/A');
    expect(formatMatchScore(undefined)).toBe('N/A');
  });
});

describe('truncateText', () => {
  test('truncates text longer than maxLength', () => {
    const longText = 'This is a long text that should be truncated';
    expect(truncateText(longText, 10)).toBe('This is a ...');
  });

  test('does not truncate text shorter than or equal to maxLength', () => {
    const shortText = 'Short text';
    expect(truncateText(shortText, 20)).toBe(shortText);
  });

  test('uses default maxLength of 100 if not provided', () => {
    const longText = 'a'.repeat(120);
    expect(truncateText(longText)).toBe('a'.repeat(100) + '...');
  });

  test('returns empty string for null or undefined', () => {
    expect(truncateText(null)).toBe('');
    expect(truncateText(undefined)).toBe('');
  });
});

describe('formatDuration', () => {
  test('formats duration string with hours, minutes, and seconds', () => {
    expect(formatDuration('1:30:45.123456')).toBe('1 hour 30 minutes 45 seconds');
  });

  test('handles plural and singular correctly', () => {
    expect(formatDuration('1:01:01.000000')).toBe('1 hour 1 minute 1 second');
    expect(formatDuration('2:02:02.000000')).toBe('2 hours 2 minutes 2 seconds');
  });

  test('returns full string for invalid format', () => {
    expect(formatDuration('invalid')).toBe('invalid');
  });

  test('returns N/A for null or undefined', () => {
    expect(formatDuration(null)).toBe('N/A');
    expect(formatDuration(undefined)).toBe('N/A');
  });
});