import { useLocation } from "react-router-dom";
import { DumpInput } from "../features/entry-dump/DumpInput";

export function DumpPage() {
  const location = useLocation();
  const draft = (location.state as { draft?: string } | null)?.draft;

  return (
    <div
      style={{
        padding: "1.2em",
        flex: 1,
        display: "flex",
        flexDirection: "column",
        justifyContent: "safe center",
        minHeight: 0,
      }}
    >
      <DumpInput initialText={draft} />
    </div>
  );
}
