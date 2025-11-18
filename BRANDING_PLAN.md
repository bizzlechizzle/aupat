# Abandoned Upstate Branding Implementation Plan

## Overview
Step-by-step plan to import and apply Abandoned Upstate branding to the AUPAT desktop application.

## Current Brand Assets

### Logo
- **File**: `/home/user/aupat/Abandoned Upstate.png`
- **Style**: Bold italic condensed sans-serif (Impact-style)
- **Colors**: Black background, white text
- **Elements**: New York state silhouette integrated into design
- **Format**: PNG with transparency

## Brand Identity Analysis

### Color Palette (from logo)
```css
/* Primary Colors */
--brand-black: #000000;       /* Background, primary text */
--brand-white: #FFFFFF;       /* Logo text, highlights */

/* Suggested Accent Colors (to be confirmed from website) */
--brand-gray-dark: #1a1a1a;   /* Subtle backgrounds */
--brand-gray-medium: #666666; /* Secondary text */
--brand-gray-light: #e5e5e5;  /* Borders, dividers */
```

### Typography
```css
/* Primary Font (Logo Style) */
font-family: Impact, "Arial Black", "Helvetica Inserat", sans-serif;
font-weight: 900;
font-style: italic;
letter-spacing: -0.02em;
text-transform: uppercase;

/* Body Font (to be confirmed) */
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
```

## Implementation Steps

### Phase 1: Asset Collection (MANUAL - requires website access)
Since abandonedupstate.com archive is referenced but not in this repo, you'll need to:

1. **Visit abandonedupstate.com** (or archived version if offline)
2. **Extract Color Palette**:
   - Use browser DevTools to inspect CSS variables
   - Take screenshots of key pages
   - Note: Primary, secondary, accent colors
3. **Identify Typography**:
   - Inspect font-family declarations
   - Note font weights and sizes used
   - Check for any custom web fonts (Google Fonts, etc.)
4. **Collect Additional Assets**:
   - Favicon
   - Any icon sets used
   - Background patterns/textures
   - Button styles and hover states

### Phase 2: Asset Integration

#### 2.1 Copy Logo to Desktop App
```bash
# Create assets directory if needed
mkdir -p desktop/src/renderer/assets/images

# Copy logo with proper naming
cp "Abandoned Upstate.png" desktop/src/renderer/assets/images/abandoned-upstate-logo.png
```

#### 2.2 Create Theme Configuration
Create `desktop/src/renderer/theme.css`:
```css
:root {
  /* Brand Colors */
  --au-black: #000000;
  --au-white: #FFFFFF;
  --au-gray-900: #1a1a1a;
  --au-gray-800: #2d2d2d;
  --au-gray-700: #404040;
  --au-gray-600: #666666;
  --au-gray-500: #808080;
  --au-gray-400: #999999;
  --au-gray-300: #b3b3b3;
  --au-gray-200: #cccccc;
  --au-gray-100: #e5e5e5;
  --au-gray-50: #f5f5f5;

  /* Brand Accent (if identified from website) */
  --au-accent: #your-accent-color;
  --au-accent-hover: #your-accent-hover;

  /* Typography */
  --font-brand: Impact, "Arial Black", "Helvetica Inserat", sans-serif;
  --font-body: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-mono: "Menlo", "Monaco", "Courier New", monospace;
}
```

#### 2.3 Update Tailwind Configuration
Modify `desktop/tailwind.config.js`:
```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        'au-black': '#000000',
        'au-white': '#FFFFFF',
        'au-gray': {
          50: '#f5f5f5',
          100: '#e5e5e5',
          200: '#cccccc',
          300: '#b3b3b3',
          400: '#999999',
          500: '#808080',
          600: '#666666',
          700: '#404040',
          800: '#2d2d2d',
          900: '#1a1a1a',
        },
        'au-accent': 'var(--au-accent)',
      },
      fontFamily: {
        'brand': ['Impact', 'Arial Black', 'Helvetica Inserat', 'sans-serif'],
        'body': ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
    },
  },
}
```

### Phase 3: UI Component Updates

#### 3.1 Header/Logo Component
Create `desktop/src/renderer/components/AppHeader.svelte`:
```svelte
<script>
  import logoSrc from '../assets/images/abandoned-upstate-logo.png';
</script>

<header class="bg-au-black border-b border-au-gray-800 px-6 py-4">
  <div class="flex items-center gap-4">
    <img src={logoSrc} alt="Abandoned Upstate" class="h-12" />
    <div>
      <h1 class="text-au-white font-brand text-2xl uppercase italic tracking-tight">
        AUPAT
      </h1>
      <p class="text-au-gray-400 text-xs">
        Location Archive Tool
      </p>
    </div>
  </div>
</header>
```

#### 3.2 Navigation Bar
Update sidebar/navigation with brand colors:
- Background: `bg-au-gray-900`
- Active item: `bg-au-black text-au-white`
- Hover: `hover:bg-au-gray-800`
- Text: `text-au-gray-300`

#### 3.3 Buttons
Update button styles:
```svelte
<!-- Primary Button -->
<button class="bg-au-black text-au-white hover:bg-au-gray-900 px-4 py-2 rounded font-medium">
  Primary Action
</button>

<!-- Secondary Button -->
<button class="bg-au-gray-800 text-au-white hover:bg-au-gray-700 px-4 py-2 rounded">
  Secondary
</button>

<!-- Danger Button -->
<button class="bg-red-600 text-white hover:bg-red-700 px-4 py-2 rounded">
  Delete
</button>
```

#### 3.4 Table Styling
Update LocationsList.svelte table:
- Header: `bg-au-gray-900 text-au-gray-300`
- Row hover: `hover:bg-au-gray-50`
- Border: `border-au-gray-200`

#### 3.5 Forms
Update input fields:
```svelte
<input
  class="border border-au-gray-300 bg-white text-au-black placeholder-au-gray-500
         focus:border-au-black focus:ring-2 focus:ring-au-gray-200"
/>
```

### Phase 4: Map Customization

#### 4.1 Custom Map Marker Icon
Create New York state silhouette marker:
```javascript
// In Map.svelte
const nyStateIcon = L.divIcon({
  html: `<div class="marker-icon">
    <svg viewBox="0 0 20 20" class="w-6 h-6 fill-au-black">
      <!-- NY state silhouette SVG path -->
    </svg>
  </div>`,
  className: 'custom-marker',
  iconSize: [24, 24],
});
```

#### 4.2 Map Tile Layer Theme
Use dark/monochrome map tiles to match brand:
```javascript
// CartoDB Dark Matter or custom styled tiles
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
  attribution: '&copy; OpenStreetMap, &copy; CartoDB'
});
```

### Phase 5: Testing & Refinement

#### 5.1 Visual Testing Checklist
- [ ] Logo displays correctly in header
- [ ] All text uses brand fonts
- [ ] Color contrast meets WCAG AA standards
- [ ] Dark mode consistency (if applicable)
- [ ] Map markers use custom NY state icon
- [ ] Buttons match brand style
- [ ] Forms have consistent styling

#### 5.2 Accessibility Check
```bash
# Install accessibility linter
npm install --save-dev eslint-plugin-jsx-a11y

# Check color contrast ratios
# Black on white: 21:1 (AAA)
# Gray-600 on white: 5.74:1 (AA)
```

## File Structure After Implementation

```
desktop/
├── src/
│   ├── renderer/
│   │   ├── assets/
│   │   │   └── images/
│   │   │       └── abandoned-upstate-logo.png
│   │   ├── components/
│   │   │   └── AppHeader.svelte
│   │   ├── lib/
│   │   │   ├── Map.svelte (updated with custom markers)
│   │   │   ├── LocationsList.svelte (updated styling)
│   │   │   └── LocationForm.svelte (updated styling)
│   │   ├── theme.css (new)
│   │   └── index.html (import theme.css)
│   └── tailwind.config.js (updated)
└── package.json
```

## Next Steps

1. **Manual Research Required**:
   - Access abandonedupstate.com to extract exact colors/fonts
   - Document findings in this file under "Website Branding Details" section

2. **Implementation**:
   - Follow Phase 2-5 steps in order
   - Test each component after updating
   - Commit changes with clear messages

3. **Validation**:
   - Compare side-by-side with abandonedupstate.com
   - Ensure brand consistency across all views
   - Get user approval on final styling

## Website Branding Details (TO BE FILLED)

```
TODO: After visiting abandonedupstate.com, document:

Primary Font:
  Family:
  Weights:
  Source:

Body Font:
  Family:
  Weights:
  Source:

Primary Color:
  Hex:
  Usage:

Secondary Color:
  Hex:
  Usage:

Accent Color:
  Hex:
  Usage:

Background Color:
  Hex:

Button Styles:
  Primary:
  Secondary:
  Hover Effect:

Icon Style:
  (describe)

Additional Notes:
  (any unique design elements)
```

## References

- Logo: `/home/user/aupat/Abandoned Upstate.png`
- Tailwind CSS Docs: https://tailwindcss.com/docs
- Svelte Styling: https://svelte.dev/docs/element-directives#style
- Leaflet Custom Markers: https://leafletjs.com/reference.html#divicon
