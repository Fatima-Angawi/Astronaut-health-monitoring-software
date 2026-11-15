/**
 * Card surface shared by every dashboard. Keeps the existing `.panel` styling
 * (rounded corner, translucent surface, backdrop blur) in one place.
 */
export default function Panel({ as: Tag = "section", className = "", children, ...rest }) {
  return (
    <Tag className={`panel ${className}`.trim()} {...rest}>
      {children}
    </Tag>
  );
}
