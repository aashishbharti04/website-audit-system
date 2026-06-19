import { Github, Globe, Mail } from "lucide-react";

export function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="mt-10 border-t pt-6 text-sm text-muted-foreground">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="font-bold text-foreground">🩺 Website Audit &amp; Recommendation System</div>
          <p className="mt-1 max-w-md text-xs">
            Crawls a website and generates a branded, prioritised audit across SEO, performance,
            content, local SEO, UX and accessibility — exportable as PDF, Word &amp; HTML.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <a href="https://github.com/aashishbharti04/website-audit-recommendation-system" target="_blank" rel="noopener"
            className="grid h-9 w-9 place-items-center rounded-lg border hover:border-primary hover:text-primary" aria-label="GitHub">
            <Github className="h-4 w-4" />
          </a>
          <a href="https://seotuners.com" target="_blank" rel="noopener"
            className="grid h-9 w-9 place-items-center rounded-lg border hover:border-primary hover:text-primary" aria-label="Website">
            <Globe className="h-4 w-4" />
          </a>
          <a href="mailto:hello@seotuners.com"
            className="grid h-9 w-9 place-items-center rounded-lg border hover:border-primary hover:text-primary" aria-label="Email">
            <Mail className="h-4 w-4" />
          </a>
        </div>
      </div>
      <div className="mt-5 flex flex-col gap-2 border-t pt-4 text-xs sm:flex-row sm:items-center sm:justify-between">
        <span>© {year} Website Audit &amp; Recommendation System. All rights reserved.</span>
        <span>Performance data via Google PageSpeed Insights · Analysis by Claude</span>
      </div>
    </footer>
  );
}
