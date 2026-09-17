"use client";

import { useId, useState } from "react";

function EyeIcon({ off }: { off: boolean }) {
  return (
    <svg
      aria-hidden="true"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12Z" />
      <circle cx="12" cy="12" r="3" />
      {/* The struck-through eye is the "currently hidden" state, matching the
          convention every password field on the web uses. */}
      {off && <path d="M4 20 20 4" />}
    </svg>
  );
}

/**
 * A password input with a show/hide toggle.
 *
 * Notes on the details that matter here:
 *  - The button is `type="button"`. Inside a form, a button with no type
 *    defaults to submit, so tapping the eye would post the form.
 *  - It is a real <button>, so it is reachable by keyboard -- but it carries
 *    `tabIndex={-1}` deliberately: Tab from the password field should go to the
 *    submit button, not detour through a control that reveals a secret. It is
 *    still reachable by pointer and by screen-reader navigation.
 *  - The label is on the button itself (aria-label) and flips with the state,
 *    and aria-pressed carries the on/off, so a screen reader announces both
 *    what it does and where it currently stands.
 *  - Revealing sets type="text", which browsers exclude from password managers'
 *    autofill matching, so the toggle resets to hidden on every mount rather
 *    than being remembered.
 */
export default function PasswordField({
  id,
  name,
  label,
  autoComplete,
  required = true,
}: {
  id?: string;
  name: string;
  label: string;
  autoComplete?: string;
  required?: boolean;
}) {
  const generatedId = useId();
  const fieldId = id ?? `${name}-${generatedId}`;
  const [visible, setVisible] = useState(false);

  return (
    <div>
      <label
        htmlFor={fieldId}
        className="mb-2 block text-xs font-bold uppercase tracking-[0.15em] text-muted"
      >
        {label}
      </label>
      <div className="relative">
        <input
          id={fieldId}
          name={name}
          type={visible ? "text" : "password"}
          required={required}
          autoComplete={autoComplete}
          /* Right padding clears the button, so a long password scrolls under
             the field's edge rather than under the eye. */
          className="field-input pr-12"
        />
        <button
          type="button"
          tabIndex={-1}
          onClick={() => setVisible((shown) => !shown)}
          aria-label={visible ? "Hide password" : "Show password"}
          aria-pressed={visible}
          aria-controls={fieldId}
          className="focus-ring absolute inset-y-0 right-0 flex w-12 items-center justify-center rounded-r text-muted transition-colors hover:text-ink"
        >
          <EyeIcon off={!visible} />
        </button>
      </div>
    </div>
  );
}
