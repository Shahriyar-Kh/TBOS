// ============================================================
// components/layout/Footer.tsx
// ============================================================

import Link from "next/link";
import { GraduationCap, Github, Twitter, Linkedin } from "lucide-react";

const FOOTER_LINKS = {
  Platform: [
    { label: "Courses", href: "/courses" },
    { label: "Instructors", href: "/instructors" },
    { label: "Pricing", href: "/pricing" },
  ],
  Company: [
    { label: "About", href: "/about" },
    { label: "Blog", href: "/blog" },
    { label: "Careers", href: "/careers" },
  ],
  Support: [
    { label: "Help Center", href: "/help" },
    { label: "Contact", href: "/contact" },
    { label: "Status", href: "/status" },
  ],
  Legal: [
    { label: "Privacy", href: "/privacy" },
    { label: "Terms", href: "/terms" },
    { label: "Cookies", href: "/cookies" },
  ],
};

export function Footer() {
  return (
    <footer className="border-t border-border bg-slate-50 dark:bg-slate-950">
      <div className="section-container py-14">
        <div className="grid grid-cols-2 gap-10 md:grid-cols-6">
          {/* Brand */}
          <div className="col-span-2">
            <Link href="/" className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-500">
                <GraduationCap className="text-white" size={18} />
              </div>
              <span className="font-display text-lg font-bold tracking-tight">
                TechBuilt<span className="text-brand-500">OS</span>
              </span>
            </Link>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-muted-foreground">
              Open education for everyone. Learn from world-class instructors
              and build the skills that matter.
            </p>
            <div className="mt-5 flex gap-3">
              {[
                { icon: <Github size={16} />, href: "#", label: "GitHub" },
                { icon: <Twitter size={16} />, href: "#", label: "Twitter" },
                { icon: <Linkedin size={16} />, href: "#", label: "LinkedIn" },
              ].map(({ icon, href, label }) => (
                <a
                  key={label}
                  href={href}
                  aria-label={label}
                  className="flex h-9 w-9 items-center justify-center rounded-lg border border-border text-slate-400 transition-colors hover:border-brand-500 hover:text-brand-500"
                >
                  {icon}
                </a>
              ))}
            </div>
          </div>

          {/* Link columns */}
          {Object.entries(FOOTER_LINKS).map(([section, links]) => (
            <div key={section}>
              <h3 className="mb-4 text-xs font-semibold uppercase tracking-widest text-slate-400">
                {section}
              </h3>
              <ul className="space-y-2.5">
                {links.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-border pt-8 text-xs text-muted-foreground sm:flex-row">
          <p>© {new Date().getFullYear()} TechBuilt Open School. All rights reserved.</p>
          <p>Built with ♥ for learners everywhere</p>
        </div>
      </div>
    </footer>
  );
}
