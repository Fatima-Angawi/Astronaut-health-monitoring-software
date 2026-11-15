import useApi from "../../hooks/useApi";
import { getValues } from "../../api";
import Async from "../../components/common/Async";

/**
 * "Why?" panel: for the value ids behind an alert or action, shows what each value is and
 * where it comes from (source document, page, quote). Values without a source are shown as
 * team design / assumption, as the knowledge base records them.
 */
export default function WhyPanel({ ids }) {
  const state = useApi(() => getValues(ids), [ids.join(",")], ids.length > 0);
  if (ids.length === 0) return <p className="async-note">No sources are attached to this alert.</p>;
  return (
    <div className="why-panel">
      <Async state={state}>
        {(d) =>
          d.items.map((v) => (
            <div key={v.value_id}>
              <strong>
                {v.value_id} · {v.field}
              </strong>
              : {v.value}
              {v.unit ? ` ${v.unit}` : ""}
              <div>
                <small>
                  {v.value_type}
                  {v.source_doc ? ` · ${v.source_doc}` : " · no external source (team design / assumption)"}
                  {v.pdf_page ? ` · page ${v.pdf_page}` : ""}
                  {v.status ? ` · ${v.status}` : ""}
                </small>
              </div>
              {v.quote && <blockquote>“{v.quote}”</blockquote>}
            </div>
          ))
        }
      </Async>
    </div>
  );
}
