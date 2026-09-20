import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Unwraps raw JSON strings, strips markdown code blocks, and returns clean human-readable prose.
 */
export function formatAgentText(text?: string | null, preferredKey?: string): string {
  if (!text) return '';
  let clean = String(text).trim();

  // Strip leading/trailing markdown code fences ```json ... ``` or ``` ... ```
  if (clean.startsWith('```')) {
    clean = clean.replace(/^```[a-z]*\s*\n?/i, '').replace(/\n?```\s*$/, '').trim();
  }

  // If text looks like JSON, attempt parsing
  if ((clean.startsWith('{') && clean.endsWith('}')) || (clean.startsWith('[') && clean.endsWith(']'))) {
    try {
      const parsed = JSON.parse(clean);
      if (typeof parsed === 'object' && parsed !== null) {
        if (Array.isArray(parsed)) {
          return parsed.map((item) => formatAgentText(typeof item === 'string' ? item : JSON.stringify(item))).join('\n');
        }
        if (preferredKey && parsed[preferredKey]) {
          return formatAgentText(parsed[preferredKey]);
        }
        const extracted =
          parsed.reasoning ||
          parsed.qualification ||
          parsed.message ||
          parsed.content ||
          parsed.body ||
          parsed.email_body ||
          parsed.strategy ||
          parsed.angle ||
          parsed.instructions_for_copywriter ||
          parsed.summary ||
          parsed.prospect_summary ||
          parsed.output ||
          parsed.text;
        if (extracted) {
          return formatAgentText(extracted);
        }
      }
    } catch {
      // If parsing fails, fall through
    }
  }

  // Also check if there is an embedded JSON block inside the text
  const startBrace = clean.indexOf('{');
  const endBrace = clean.lastIndexOf('}');
  if (startBrace !== -1 && endBrace !== -1 && endBrace > startBrace) {
    try {
      const sub = clean.slice(startBrace, endBrace + 1);
      const parsed = JSON.parse(sub);
      if (typeof parsed === 'object' && parsed !== null) {
        const extracted =
          (preferredKey && parsed[preferredKey]) ||
          parsed.reasoning ||
          parsed.qualification ||
          parsed.message ||
          parsed.content ||
          parsed.body ||
          parsed.email_body ||
          parsed.strategy ||
          parsed.angle ||
          parsed.instructions_for_copywriter ||
          parsed.summary ||
          parsed.output;
        if (extracted) {
          return formatAgentText(extracted);
        }
      }
    } catch {
      // continue
    }
  }

  // Clean unicode replacement characters and placeholder tags
  clean = clean
    .replace(/\ufffd/g, '-')
    .replace(/\[Your Name\]/g, 'Autonomous SDR Team')
    .replace(/\[Sender Name\]/g, 'Autonomous SDR Team');

  return clean.trim();
}

