'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { SITE } from '@/config/site';
import { ThemeToggle } from './ThemeToggle';
import { IconMenu, IconX, IconSearch, IconArchive } from './icons/Icon';

export function Header() {
  const pathname = usePathname();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const isActive = (path: string) => {
    const currentPathArray = pathname.split('/').filter(p => p.trim());
    const pathArray = path.split('/').filter(p => p.trim());
    return pathname === path || currentPathArray[0] === pathArray[0];
  };

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  return (
    <header className="w-full bg-background text-foreground dark:bg-background dark:text-foreground">
      <a
        id="skip-to-content"
        href="#main-content"
        className="absolute start-16 -top-full z-50 bg-background px-3 py-2 text-accent backdrop-blur-lg transition-all focus:top-4"
      >
        Skip to content
      </a>
      <div
        id="nav-container"
        className="flex w-full flex-col items-center px-4 sm:px-32"
      >
        <div
          id="top-nav-wrap"
          className="relative flex w-full flex-col items-center gap-2 text-foreground pt-4 pb-2 sm:pt-5 sm:pb-3"
        >
          <Link href="/" className="py-1 text-center text-foreground">
            <span className="site-title block">{SITE.title}</span>
            <span className="mt-1 block text-sm font-medium uppercase tracking-[0.12em] text-accent sm:text-base">
              {SITE.tagline}
            </span>
          </Link>
          <nav
            id="nav-menu"
            className="flex w-full flex-col items-center sm:py-0"
          >
            <button
              id="menu-btn"
              onClick={toggleMenu}
              className="focus-outline self-center p-2 sm:hidden"
              aria-label={isMenuOpen ? 'Close Menu' : 'Open Menu'}
              aria-expanded={isMenuOpen}
              aria-controls="menu-items"
            >
              {isMenuOpen ? (
                <IconX className="text-foreground" />
              ) : (
                <IconMenu className="text-foreground" />
              )}
            </button>
            <ul
              id="menu-items"
              className={`
                mt-2 grid w-44 grid-cols-2 place-content-center gap-2
                [&>li>a]:block [&>li>a]:px-4 [&>li>a]:py-3 [&>li>a]:text-center [&>li>a]:font-medium [&>li>a]:text-foreground [&>li>a]:hover:text-accent sm:[&>li>a]:px-2 sm:[&>li>a]:py-1
                ${isMenuOpen ? '' : 'hidden'}
                sm:mt-0 sm:flex sm:w-auto sm:justify-center sm:gap-x-5 sm:gap-y-0
              `}
            >
              <li className="col-span-2">
                <Link
                  href="/posts"
                  className={isActive('/posts') ? 'active-nav' : ''}
                >
                  Locations
                </Link>
              </li>
              {SITE.showArchives && (
                <li className="col-span-2">
                  <Link
                    href="/archives"
                    className={`focus-outline flex justify-center p-3 sm:p-1 text-foreground hover:text-foreground/80 ${
                      isActive('/archives') ? 'active-nav [&>svg]:stroke-accent' : ''
                    }`}
                    aria-label="archives"
                    title="Archives"
                  >
                    <IconArchive className="hidden sm:inline-block" />
                    <span className="sm:sr-only">Archives</span>
                  </Link>
                </li>
              )}
              <li className="col-span-1 flex items-center justify-center">
                <Link
                  href="/search"
                  className={`focus-outline flex p-3 sm:p-1 text-foreground hover:text-foreground/80 ${
                    isActive('/search') ? '[&>svg]:stroke-accent' : ''
                  }`}
                  aria-label="search"
                  title="Search"
                >
                  <IconSearch />
                  <span className="sr-only">Search</span>
                </Link>
              </li>
              {SITE.lightAndDarkMode && (
                <li className="col-span-1 flex items-center justify-center">
                  <ThemeToggle />
                </li>
              )}
            </ul>
          </nav>
        </div>
      </div>
      <div className="w-full px-4 sm:px-32">
        <div className="mx-auto w-full max-w-app">
          <hr className="my-0 w-full border-accent" aria-hidden="true" />
        </div>
      </div>
    </header>
  );
}
