import ReactMarkdown, { type Components } from "react-markdown";

const COMPONENTS: Components = {
  p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
  strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
  em: ({ children }) => <em className="text-muted-foreground">{children}</em>,
  ul: ({ children }) => <ul className="mb-3 ml-5 list-disc space-y-1 last:mb-0">{children}</ul>,
  ol: ({ children }) => <ol className="mb-3 ml-5 list-decimal space-y-1 last:mb-0">{children}</ol>,
  a: ({ children, href }) => (
    <a href={href} target="_blank" rel="noreferrer" className="text-primary underline underline-offset-2">
      {children}
    </a>
  ),
  code: ({ children }) => <code className="rounded bg-muted px-1 py-0.5 font-mono text-[0.8em]">{children}</code>,
  h1: ({ children }) => <p className="mb-2 font-semibold">{children}</p>,
  h2: ({ children }) => <p className="mb-2 font-semibold">{children}</p>,
  h3: ({ children }) => <p className="mb-2 font-semibold">{children}</p>,
  img: () => null,
};

export function AnswerText({ text }: { text: string }) {
  return (
    <div className="text-sm leading-relaxed">
      <ReactMarkdown components={COMPONENTS}>{text}</ReactMarkdown>
    </div>
  );
}
