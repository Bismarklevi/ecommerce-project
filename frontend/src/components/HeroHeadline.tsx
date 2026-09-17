// Splits a headline into per-word spans so each one can rise in on its own
// beat. Server-rendered: the stagger is CSS animation-delay on markup that
// ships with the document, so there is no client bundle to wait for and no
// flash of an unsplit heading.
//
// Splitting on spaces keeps the text one uninterrupted string for a screen
// reader -- the whitespace between words survives as real text nodes, so the
// heading is still read as a sentence rather than a list of words.

const WORD_STAGGER_MS = 70;

export default function HeroHeadline({
  text,
  blockWord,
  className,
  startDelayMs = 80,
}: {
  text: string;
  /** Word to set in the solid colour block, matched case-insensitively. */
  blockWord?: string;
  className?: string;
  startDelayMs?: number;
}) {
  const words = text.split(" ");
  const blockIndex = blockWord
    ? words.findIndex((word) => word.toLowerCase() === blockWord.toLowerCase())
    : -1;

  return (
    <h1 className={className}>
      {words.map((word, index) => (
        // The key is index-based on purpose: the same word can legitimately
        // appear twice in a headline, and the list never reorders.
        <span key={index}>
          <span
            className="hero-word"
            style={{ animationDelay: `${startDelayMs + index * WORD_STAGGER_MS}ms` }}
          >
            {index === blockIndex ? <span className="text-block">{word}</span> : word}
          </span>
          {index < words.length - 1 ? " " : null}
        </span>
      ))}
    </h1>
  );
}
