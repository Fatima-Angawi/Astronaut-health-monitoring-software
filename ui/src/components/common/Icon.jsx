/**
 * Palette-driven icon.
 *
 * The Figma export ships every icon as an SVG with a hard-coded stroke colour, and an <img>
 * cannot be re-coloured or animated. `Icon` paints the same artwork through a CSS mask: the
 * SVG supplies the shape, `background-color` supplies the colour, and because that colour is
 * `currentColor` the icon follows its hover, focus and active states.
 *
 * `tone` states the *meaning* of the icon rather than decorating it (palette in index.css):
 *   nav | info  blue      navigation, information, interactive elements
 *   success     green     a completed, healthy state
 *   warning     yellow    needs attention
 *   critical    red       a critical alert
 *   muted       neutral   secondary or inactive
 *
 * The astronaut logo and the two-tone status dot stay plain <img> elements: they are artwork
 * with several tones, which a mask would flatten into one silhouette.
 */
export default function Icon({ src, size = 24, tone = "nav", className = "" }) {
  return (
    <span
      className={`icon icon--${tone}${className ? ` ${className}` : ""}`}
      style={{ "--icon-src": `url("${src}")`, "--icon-size": `${size}px` }}
      aria-hidden="true"
    />
  );
}
