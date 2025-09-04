/**
 * Formats an ISO 8601 date string or a Date object into DD.MM.YYYY HH:MM format.
 * Handles null or undefined input by returning a placeholder.
 *
 * @param dateInput The date string (ISO 8601) or Date object to format.
 * @param placeholder The string to return if the input is invalid or null/undefined. Defaults to 'N/A'.
 * @returns The formatted date string or the placeholder.
 */
export function formatDateTime(
  dateInput: string | Date | null | undefined,
  placeholder: string = 'N/A'
): string {
  if (!dateInput) {
    return placeholder;
  }

  try {
    const date = typeof dateInput === 'string' ? new Date(dateInput) : dateInput;

    // Check if the date is valid after parsing
    if (isNaN(date.getTime())) {
      console.warn(`Invalid date input provided to formatDateTime: ${dateInput}`);
      return placeholder;
    }

    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0'); // Month is 0-indexed
    const year = date.getFullYear();
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');

    return `${day}.${month}.${year} ${hours}:${minutes}`;
  } catch (error) {
    console.error(`Error formatting date: ${dateInput}`, error);
    return placeholder;
  }
}
