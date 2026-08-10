import { useEffect, useRef, type TextareaHTMLAttributes } from "react";

export function AutoTextarea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [props.value]);

  return <textarea ref={ref} {...props} style={{ overflow: "hidden", ...props.style }} />;
}
