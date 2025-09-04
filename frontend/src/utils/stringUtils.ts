/**
 * Normalizes a string by converting it to lowercase and removing common Czech/Slovak diacritics.
 * Returns an empty string if the input is null or undefined.
 *
 * @param str - The string to normalize.
 * @returns The normalized string.
 */
export function normalizeString(str: string | null | undefined): string {
  if (!str) {
    return '';
  }
  // Manual replacement for common characters - extend if needed
  return str.toLowerCase()
      .replace(/[áčďéěíňóřšťúůýž]/g, (char) => {
        const map: { [key: string]: string } = {
          'á': 'a', 'č': 'c', 'ď': 'd', 'é': 'e', 'ě': 'e', 'í': 'i',
          'ň': 'n', 'ó': 'o', 'ř': 'r', 'š': 's', 'ť': 't', 'ú': 'u',
          'ů': 'u', 'ý': 'y', 'ž': 'z'
        };
        return map[char] || char;
      });
} 