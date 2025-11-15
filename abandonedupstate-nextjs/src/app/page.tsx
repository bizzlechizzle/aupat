import { SITE } from '@/config/site';

export default function HomePage() {
  return (
    <section className="py-12">
      <div className="text-center mb-12">
        <h1 className="site-title mb-4">{SITE.title}</h1>
        <p className="post-tagline post-tagline--featured">
          {SITE.tagline}
        </p>
        <p className="text-foreground max-w-2xl mx-auto">
          {SITE.description}
        </p>
      </div>

      <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3 max-w-6xl mx-auto px-4">
        {/* Placeholder cards - will be replaced with actual location cards */}
        <div className="border border-border rounded-lg p-6 hover:border-accent transition-colors">
          <h3 className="mb-2">Featured Locations</h3>
          <p className="text-foreground/80">
            Explore our collection of abandoned and historical sites across upstate regions.
          </p>
        </div>

        <div className="border border-border rounded-lg p-6 hover:border-accent transition-colors">
          <h3 className="mb-2">Recent Discoveries</h3>
          <p className="text-foreground/80">
            Check out the latest locations we've documented and photographed.
          </p>
        </div>

        <div className="border border-border rounded-lg p-6 hover:border-accent transition-colors">
          <h3 className="mb-2">Browse Archives</h3>
          <p className="text-foreground/80">
            Search through our comprehensive archive of abandoned structures.
          </p>
        </div>
      </div>

      <div className="mt-16 text-center">
        <h2 className="mb-6">About This Project</h2>
        <div className="max-w-3xl mx-auto app-prose px-4">
          <p>
            This site documents abandoned and historical locations, preserving their stories through photography and detailed research. Each location represents a piece of history worth remembering.
          </p>
          <p>
            We approach these sites with respect, documenting their current state while honoring their past. Our goal is to create a comprehensive archive that serves as both a historical record and a testament to the passage of time.
          </p>
        </div>
      </div>

      <div className="mt-16">
        <h2 className="text-center mb-8">Theme Toggle Test</h2>
        <div className="max-w-2xl mx-auto px-4">
          <p className="mb-4">
            Use the theme toggle in the header to switch between light and dark modes. The theme preference is saved in your browser's local storage.
          </p>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="p-6 bg-muted rounded-lg">
              <h4 className="text-accent mb-2">Light Mode</h4>
              <p className="text-sm text-foreground/80">
                Cream background (#fffbf7) with dark text and warm brown accents (#b9975c).
              </p>
            </div>
            <div className="p-6 bg-muted rounded-lg">
              <h4 className="text-accent mb-2">Dark Mode</h4>
              <p className="text-sm text-foreground/80">
                Dark gray background (#474747) with light text and the same warm accents.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
