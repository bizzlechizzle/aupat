/**
 * AUPAT Desktop - Browser Manager
 *
 * Manages embedded Chromium browser (WebContentsView) for web archiving.
 * Handles browser lifecycle, navigation, cookie management, and IPC communication.
 *
 * Security:
 * - Separate session partition for cookie isolation
 * - Context isolation enabled
 * - Node integration disabled
 * - Sandbox enabled
 *
 * Version: 0.1.2-browser
 * Last Updated: 2025-11-18
 */

import { BrowserView } from 'electron';
import log from 'electron-log';

export class BrowserManager {
  constructor(mainWindow) {
    this.mainWindow = mainWindow;
    this.view = null;
    this.currentUrl = '';
    this.currentTitle = '';
  }

  /**
   * Create browser view with security settings.
   *
   * Uses separate session partition to isolate cookies from main app.
   * View is created lazily when first needed.
   *
   * Returns:
   *   BrowserView instance or null if creation fails
   */
  create() {
    if (this.view) {
      log.info('BrowserView already exists, reusing');
      return this.view;
    }

    try {
      this.view = new BrowserView({
        webPreferences: {
          partition: 'persist:aupat-browser',
          contextIsolation: true,
          nodeIntegration: false,
          sandbox: true,
          webSecurity: true,
          allowRunningInsecureContent: false,
          javascript: true
        }
      });

      this.mainWindow.setBrowserView(this.view);
      this.setupEventListeners();

      log.info('BrowserView created successfully');
      return this.view;

    } catch (error) {
      log.error('Failed to create BrowserView:', error);
      this.view = null;
      return null;
    }
  }

  /**
   * Set up event listeners for browser view.
   *
   * Tracks navigation, page title changes, and media detection.
   * Emits IPC events to renderer process for UI updates.
   */
  setupEventListeners() {
    if (!this.view) return;

    const webContents = this.view.webContents;

    // Store listener references for cleanup
    this.listeners = {};

    // Track URL changes
    this.listeners.didNavigate = (event, url) => {
      this.currentUrl = url;
      this.mainWindow.webContents.send('browser:url-changed', url);
      log.info(`Browser navigated to: ${url}`);
    };
    webContents.on('did-navigate', this.listeners.didNavigate);

    // Track in-page navigation (anchors, history)
    this.listeners.didNavigateInPage = (event, url) => {
      this.currentUrl = url;
      this.mainWindow.webContents.send('browser:url-changed', url);
    };
    webContents.on('did-navigate-in-page', this.listeners.didNavigateInPage);

    // Track page title
    this.listeners.pageTitleUpdated = (event, title) => {
      this.currentTitle = title;
      this.mainWindow.webContents.send('browser:title-changed', title);
    };
    webContents.on('page-title-updated', this.listeners.pageTitleUpdated);

    // Track navigation state
    this.listeners.didStartLoading = () => {
      this.mainWindow.webContents.send('browser:loading', true);
    };
    webContents.on('did-start-loading', this.listeners.didStartLoading);

    this.listeners.didStopLoading = () => {
      this.mainWindow.webContents.send('browser:loading', false);
      this.updateNavigationState();
    };
    webContents.on('did-stop-loading', this.listeners.didStopLoading);

    // Handle navigation errors
    this.listeners.didFailLoad = (event, errorCode, errorDescription, validatedURL) => {
      log.error(`Browser failed to load ${validatedURL}: ${errorDescription}`);
      this.mainWindow.webContents.send('browser:error', {
        url: validatedURL,
        error: errorDescription,
        code: errorCode
      });
    };
    webContents.on('did-fail-load', this.listeners.didFailLoad);

    // Detect media on page load
    this.listeners.didFinishLoad = () => {
      this.injectMediaDetector().catch(error => {
        log.warn('Failed to inject media detector:', error);
      });
    };
    webContents.on('did-finish-load', this.listeners.didFinishLoad);

    // Handle new window requests (open in same view)
    this.listeners.windowOpenHandler = (details) => {
      this.navigate(details.url);
      return { action: 'deny' };
    };
    webContents.setWindowOpenHandler(this.listeners.windowOpenHandler);

    // Handle browser crashes (auto-restart)
    this.listeners.crashed = (event, killed) => {
      // Prevent multiple recovery attempts
      if (this.isRecovering) return;
      this.isRecovering = true;

      log.error('BrowserView crashed, attempting auto-restart...');
      this.mainWindow.webContents.send('browser:crashed');

      // Destroy crashed view
      const crashedUrl = this.currentUrl;
      this.destroy();

      // Recreate and restore URL
      setTimeout(() => {
        this.create();
        if (crashedUrl) {
          this.navigate(crashedUrl);
          log.info(`Browser restarted, restored URL: ${crashedUrl}`);
        }
        this.isRecovering = false;
      }, 1000);
    };
    webContents.on('crashed', this.listeners.crashed);

    // Handle unresponsive renderer
    this.listeners.unresponsive = () => {
      log.warn('BrowserView became unresponsive');
      this.mainWindow.webContents.send('browser:unresponsive');
    };
    webContents.on('unresponsive', this.listeners.unresponsive);

    // Handle renderer becoming responsive again
    this.listeners.responsive = () => {
      log.info('BrowserView became responsive again');
      this.mainWindow.webContents.send('browser:responsive');
    };
    webContents.on('responsive', this.listeners.responsive);
  }

  /**
   * Remove all event listeners from browser view.
   * Called before destroying the view to prevent memory leaks.
   */
  removeEventListeners() {
    if (!this.view || !this.listeners) return;

    const webContents = this.view.webContents;

    webContents.removeListener('did-navigate', this.listeners.didNavigate);
    webContents.removeListener('did-navigate-in-page', this.listeners.didNavigateInPage);
    webContents.removeListener('page-title-updated', this.listeners.pageTitleUpdated);
    webContents.removeListener('did-start-loading', this.listeners.didStartLoading);
    webContents.removeListener('did-stop-loading', this.listeners.didStopLoading);
    webContents.removeListener('did-fail-load', this.listeners.didFailLoad);
    webContents.removeListener('did-finish-load', this.listeners.didFinishLoad);
    webContents.removeListener('crashed', this.listeners.crashed);
    webContents.removeListener('unresponsive', this.listeners.unresponsive);
    webContents.removeListener('responsive', this.listeners.responsive);

    this.listeners = null;
    log.debug('Removed all event listeners from BrowserView');
  }

  /**
   * Update navigation state (canGoBack, canGoForward).
   *
   * Sends updated state to renderer process for UI controls.
   */
  updateNavigationState() {
    if (!this.view) return;

    const webContents = this.view.webContents;
    this.mainWindow.webContents.send('browser:navigation-state', {
      canGoBack: webContents.canGoBack(),
      canGoForward: webContents.canGoForward()
    });
  }

  /**
   * Inject JavaScript to detect media on page.
   *
   * Counts images and videos, sends info to main window.
   * Used for "Extract media" feature.
   */
  async injectMediaDetector() {
    if (!this.view) return;

    const script = `
      (function() {
        const images = document.querySelectorAll('img[src], img[srcset]');
        const videos = document.querySelectorAll('video[src], video source');

        const imageUrls = Array.from(images).map(img => {
          return {
            src: img.src,
            srcset: img.srcset,
            alt: img.alt,
            width: img.naturalWidth,
            height: img.naturalHeight
          };
        });

        const videoUrls = Array.from(videos).map(vid => {
          return {
            src: vid.src,
            type: vid.type
          };
        });

        return {
          imageCount: images.length,
          videoCount: videos.length,
          url: window.location.href,
          title: document.title,
          images: imageUrls.slice(0, 10),  // Limit to first 10
          videos: videoUrls.slice(0, 5)    // Limit to first 5
        };
      })();
    `;

    try {
      const mediaInfo = await this.view.webContents.executeJavaScript(script);
      this.mainWindow.webContents.send('browser:media-detected', mediaInfo);
      log.info(`Detected ${mediaInfo.imageCount} images, ${mediaInfo.videoCount} videos on page`);
    } catch (error) {
      log.warn('Media detection failed:', error);
    }
  }

  /**
   * Navigate browser to URL.
   *
   * Args:
   *   url: URL to navigate to (auto-prepends https:// if needed)
   */
  navigate(url) {
    if (!this.view) {
      log.error('Cannot navigate: BrowserView not created');
      return;
    }

    if (!url) {
      log.warn('Navigate called with empty URL');
      return;
    }

    // Auto-prepend https:// if no protocol
    let targetUrl = url.trim();
    if (!targetUrl.startsWith('http://') && !targetUrl.startsWith('https://')) {
      targetUrl = 'https://' + targetUrl;
    }

    try {
      this.view.webContents.loadURL(targetUrl);
      log.info(`Navigating to: ${targetUrl}`);
    } catch (error) {
      log.error(`Navigation failed for ${targetUrl}:`, error);
      this.mainWindow.webContents.send('browser:error', {
        url: targetUrl,
        error: error.message
      });
    }
  }

  /**
   * Navigate back in history.
   */
  goBack() {
    if (this.view && this.view.webContents.canGoBack()) {
      this.view.webContents.goBack();
      log.info('Browser navigated back');
    }
  }

  /**
   * Navigate forward in history.
   */
  goForward() {
    if (this.view && this.view.webContents.canGoForward()) {
      this.view.webContents.goForward();
      log.info('Browser navigated forward');
    }
  }

  /**
   * Reload current page.
   */
  reload() {
    if (this.view) {
      this.view.webContents.reload();
      log.info('Browser page reloaded');
    }
  }

  /**
   * Set browser view bounds (position and size).
   *
   * Args:
   *   bounds: {x, y, width, height} in pixels
   */
  setBounds(bounds) {
    if (this.view) {
      this.view.setBounds(bounds);
    }
  }

  /**
   * Get cookies for a specific domain.
   *
   * Args:
   *   domain: Domain to get cookies for (e.g., '.instagram.com')
   *
   * Returns:
   *   Promise<Cookie[]> Array of cookie objects
   */
  async getCookies(domain) {
    if (!this.view) {
      log.warn('Cannot get cookies: BrowserView not created');
      return [];
    }

    try {
      const session = this.view.webContents.session;
      const cookies = await session.cookies.get({ domain });

      log.info(`Retrieved ${cookies.length} cookies for domain: ${domain}`);
      return cookies;

    } catch (error) {
      log.error(`Failed to get cookies for ${domain}:`, error);
      return [];
    }
  }

  /**
   * Export cookies in Netscape format for ArchiveBox.
   *
   * Args:
   *   domain: Domain to export cookies for
   *
   * Returns:
   *   Promise<string> Netscape-format cookie string
   */
  async exportCookiesForArchiveBox(domain) {
    const cookies = await this.getCookies(domain);

    if (cookies.length === 0) {
      return '';
    }

    // Convert to Netscape format
    // Format: domain, flag, path, secure, expiration, name, value
    const netscapeCookies = cookies.map(cookie => {
      const domainField = cookie.domain.startsWith('.') ? cookie.domain : '.' + cookie.domain;
      const flagField = 'TRUE';  // Domain wildcard
      const pathField = cookie.path || '/';
      const secureField = cookie.secure ? 'TRUE' : 'FALSE';
      const expirationField = cookie.expirationDate
        ? Math.floor(cookie.expirationDate)
        : 0;
      const nameField = cookie.name;
      const valueField = cookie.value;

      return `${domainField}\t${flagField}\t${pathField}\t${secureField}\t${expirationField}\t${nameField}\t${valueField}`;
    }).join('\n');

    return netscapeCookies;
  }

  /**
   * Open DevTools for debugging.
   */
  openDevTools() {
    if (this.view) {
      this.view.webContents.openDevTools();
      log.info('Opened DevTools for browser');
    }
  }

  /**
   * Close DevTools.
   */
  closeDevTools() {
    if (this.view) {
      this.view.webContents.closeDevTools();
      log.info('Closed DevTools for browser');
    }
  }

  /**
   * Get current URL.
   *
   * Returns:
   *   Current URL string or empty string if no view
   */
  getCurrentUrl() {
    return this.currentUrl;
  }

  /**
   * Get current page title.
   *
   * Returns:
   *   Current title string or empty string if no view
   */
  getCurrentTitle() {
    return this.currentTitle;
  }

  /**
   * Destroy browser view and clean up resources.
   *
   * Removes view from window and frees memory.
   * Safe to call multiple times.
   */
  destroy() {
    if (this.view) {
      try {
        // Remove event listeners first to prevent memory leaks
        this.removeEventListeners();

        this.mainWindow.removeBrowserView(this.view);
        this.view.webContents.destroy();
        this.view = null;
        this.currentUrl = '';
        this.currentTitle = '';
        log.info('BrowserView destroyed');
      } catch (error) {
        log.error('Error destroying BrowserView:', error);
      }
    }
  }

  /**
   * Check if browser view is created.
   *
   * Returns:
   *   True if view exists, false otherwise
   */
  isCreated() {
    return this.view !== null;
  }
}
