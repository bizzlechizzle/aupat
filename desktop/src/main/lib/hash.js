/**
 * AUPAT Hash Module
 *
 * ONE FUNCTION: Calculate SHA256 hash of files
 *
 * LILBITS Principle: One script = one function
 * This module handles SHA256 hashing only.
 *
 * Version: 1.0.0
 * Last Updated: 2025-11-19
 */

import crypto from 'crypto';
import fs from 'fs';
import path from 'path';

/**
 * Calculate SHA256 hash of a file.
 *
 * Uses streaming to handle large files efficiently (64KB chunks).
 * Returns the full 64-character SHA256 hash. To get the 12-character
 * version used in filenames, use: hash.substring(0, 12)
 *
 * @param {string} filePath - Absolute path to the file
 * @returns {Promise<string>} Promise resolving to SHA256 hash (64-char hex string)
 * @throws {Error} If file doesn't exist, can't be read, or hashing fails
 *
 * @example
 * // Calculate hash for an image
 * const hash = await calculateSHA256('/path/to/image.jpg');
 * console.log('Full hash:', hash);           // 64 characters
 * console.log('12-char:', hash.substring(0, 12));  // First 12 characters
 *
 * @example
 * // With error handling
 * try {
 *   const hash = await calculateSHA256('/path/to/file.pdf');
 *   console.log('SHA256:', hash);
 * } catch (error) {
 *   console.error('Hashing failed:', error.message);
 * }
 */
async function calculateSHA256(filePath) {
  // Validate input
  if (!filePath || typeof filePath !== 'string') {
    throw new Error('File path must be a non-empty string');
  }

  // Check if file exists
  if (!fs.existsSync(filePath)) {
    throw new Error(`File not found: ${filePath}`);
  }

  // Check if path is actually a file (not a directory)
  const stats = fs.statSync(filePath);
  if (!stats.isFile()) {
    throw new Error(`Path is not a file: ${filePath}`);
  }

  // Calculate SHA256 using streams (memory efficient for large files)
  return new Promise((resolve, reject) => {
    const hash = crypto.createHash('sha256');
    const stream = fs.createReadStream(filePath, {
      highWaterMark: 65536  // 64KB chunks (same as Python implementation)
    });

    stream.on('data', (chunk) => {
      hash.update(chunk);
    });

    stream.on('end', () => {
      // Return full 64-character hash
      // Caller can extract 12-char version: hash.substring(0, 12)
      resolve(hash.digest('hex'));
    });

    stream.on('error', (error) => {
      reject(new Error(`Failed to hash ${filePath}: ${error.message}`));
    });
  });
}

/**
 * Calculate SHA256 synchronously (blocking).
 *
 * USE SPARINGLY: This blocks the event loop while reading the file.
 * Prefer the async calculateSHA256() for better performance.
 * Only use for small files or when you absolutely need synchronous operation.
 *
 * @param {string} filePath - Absolute path to the file
 * @returns {string} SHA256 hash (64-char hex string)
 * @throws {Error} If file doesn't exist, can't be read, or hashing fails
 *
 * @example
 * // Synchronous hashing (blocks event loop)
 * const hash = calculateSHA256Sync('/path/to/small-file.txt');
 * console.log('Hash:', hash);
 */
function calculateSHA256Sync(filePath) {
  // Validate input
  if (!filePath || typeof filePath !== 'string') {
    throw new Error('File path must be a non-empty string');
  }

  // Check if file exists
  if (!fs.existsSync(filePath)) {
    throw new Error(`File not found: ${filePath}`);
  }

  // Check if path is actually a file (not a directory)
  const stats = fs.statSync(filePath);
  if (!stats.isFile()) {
    throw new Error(`Path is not a file: ${filePath}`);
  }

  try {
    // Read entire file into memory (why this should only be used for small files)
    const buffer = fs.readFileSync(filePath);

    // Calculate and return hash
    return crypto.createHash('sha256').update(buffer).digest('hex');
  } catch (error) {
    throw new Error(`Failed to hash ${filePath}: ${error.message}`);
  }
}

// Export functions
export {
  calculateSHA256,
  calculateSHA256Sync
};
