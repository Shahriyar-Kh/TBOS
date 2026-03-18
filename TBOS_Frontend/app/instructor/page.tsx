import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function InstructorDashboardPage() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Instructor Dashboard</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground">Course creation, student management, and analytics widgets will appear here.</p>
      </CardContent>
    </Card>
  );
}
