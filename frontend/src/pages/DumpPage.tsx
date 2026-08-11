import { DumpInput } from "../features/entry-dump/DumpInput";

export function DumpPage() {
  return (
    <div
      style={{
        padding: "1.2em",
        flex: 1,
        display: "flex",
        flexDirection: "column",
        minHeight: 0,
      }}
    >
      <DumpInput />
    </div>
  );
}
