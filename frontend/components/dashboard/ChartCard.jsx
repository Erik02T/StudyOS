import SectionCard from "../ui/SectionCard";

export default function ChartCard({ title, description, children, className = "", actions }) {
  return (
    <SectionCard title={title} description={description} className={className} actions={actions}>
      <div className="h-72">{children}</div>
    </SectionCard>
  );
}
