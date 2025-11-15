/**
 * Design Tokens for Abandoned Upstate
 * Version: 0.1.1
 * Extracted from Astro site for exact brand consistency
 */

export const designTokens = {
  colors: {
    light: {
      background: '#fffbf7',    // Off-white/cream
      foreground: '#454545',    // Dark gray text
      accent: '#b9975c',        // Warm brown/tan
      muted: '#e6e6e6',         // Light gray
      border: '#b9975c',        // Same as accent
    },
    dark: {
      background: '#474747',    // Medium gray
      foreground: '#fffbf7',    // Off-white
      accent: '#b9975c',        // Warm brown/tan (consistent across themes)
      muted: '#343f60',         // Dark blue-gray
      border: '#b9975c',        // Same as accent
    },
    // Additional colors from original design
    headerLight: {
      background: '#45372b',    // Dark brown
      foreground: '#fbfbfb',    // Almost white
    },
  },

  typography: {
    fonts: {
      heading: '"Roboto Mono", ui-monospace, SFMono-Regular, Menlo, monospace',
      body: '"Lora", Georgia, serif',
      mono: '"Input Mono Narrow", "Roboto Mono", monospace', // Custom font
    },

    // Fluid typography scale using clamp()
    scale: {
      '-1': 'clamp(0.88rem, 0.82rem + 0.3vw, 0.95rem)',
      '0': 'clamp(1rem, 0.95rem + 0.4vw, 1.125rem)',
      '1': 'clamp(1.25rem, 1.1rem + 1.2vw, 1.6rem)',
      '2': 'clamp(1.6rem, 1.3rem + 2vw, 2.25rem)',
      '3': 'clamp(2.25rem, 1.6rem + 3.5vw, 3.5rem)',
    },

    // Font weights
    weights: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },

    // Letter spacing
    letterSpacing: {
      tight: '0.04em',
      normal: '0.05em',
      wide: '0.1em',
      wider: '0.12em',
    },
  },

  spacing: {
    maxWidth: {
      app: '64rem', // max-w-5xl
    },
  },

  effects: {
    // Selection colors
    selection: {
      background: 'rgba(185, 151, 92, 0.75)', // accent @ 75%
    },

    // Scrollbar
    scrollbar: {
      thumb: 'var(--color-muted)',
      track: 'transparent',
    },
  },
} as const

export type DesignTokens = typeof designTokens
