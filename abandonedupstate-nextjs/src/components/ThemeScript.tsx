/**
 * Theme initialization script
 * Runs before React hydration to prevent theme flash
 * Based on Astro site's toggle-theme.js
 */

export function ThemeScript() {
  const themeScript = `
    (function() {
      function getTheme() {
        const stored = localStorage.getItem('theme');
        if (stored) return stored;

        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        return prefersDark ? 'dark' : 'light';
      }

      const theme = getTheme();
      document.documentElement.setAttribute('data-theme', theme);
    })();
  `;

  return (
    <script
      dangerouslySetInnerHTML={{ __html: themeScript }}
      suppressHydrationWarning
    />
  );
}
