/**
 * Site configuration
 * Based on Astro site config
 */

export const SITE = {
  title: 'Abandoned Upstate',
  tagline: 'Preserving History. Documenting Decay.',
  description: 'Exploring abandoned and historical locations across upstate regions',
  author: 'Bryant Neal',
  url: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
  lightAndDarkMode: true,
  showArchives: true,
  postsPerPage: 10,
  scheduledPostMargin: 15 * 60 * 1000, // 15 minutes
} as const;

export const NAVIGATION = [
  {
    name: 'Locations',
    href: '/posts',
  },
  {
    name: 'Archives',
    href: '/archives',
    icon: 'archive',
    showInMobile: true,
  },
  {
    name: 'Search',
    href: '/search',
    icon: 'search',
    iconOnly: true,
  },
] as const;

export const SOCIAL_LINKS = {
  github: '',
  instagram: '',
  facebook: '',
  twitter: '',
  youtube: '',
} as const;
