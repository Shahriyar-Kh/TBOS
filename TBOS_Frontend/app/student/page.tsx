import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function StudentDashboardPage() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Student Dashboard</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground">Your enrolled courses, assignments, and progress will appear here.</p>
      </CardContent>
    </Card>
  );
}
