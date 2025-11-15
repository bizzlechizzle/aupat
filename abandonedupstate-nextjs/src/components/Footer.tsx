import { SITE } from '@/config/site';

export interface FooterProps {
  noMarginTop?: boolean;
}

export function Footer({ noMarginTop = false }: FooterProps) {
  const currentYear = new Date().getFullYear();

  return (
    <footer className={`w-full ${noMarginTop ? '' : 'mt-auto'}`}>
      <div className="w-full px-4 sm:px-32">
        <div className="mx-auto w-full max-w-app">
          <hr className="my-0 w-full border-accent" aria-hidden="true" />
        </div>
      </div>
      <div className="mx-auto flex w-full max-w-app flex-col items-center gap-6 px-4 py-6 text-center sm:flex-row-reverse sm:justify-center sm:gap-[32rem] sm:py-4">
        {/* Socials component will go here */}
        <div className="flex gap-4">
          {/* Placeholder for social links */}
        </div>
        <div className="my-2 flex flex-col items-center whitespace-nowrap sm:my-0 sm:flex-row sm:items-center">
          <span>Copyright &copy; {currentYear} {SITE.title}</span>
        </div>
      </div>
    </footer>
  );
}
