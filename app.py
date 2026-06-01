
import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectItem } from "@/components/ui/select";
import { motion } from "framer-motion";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

const sampleData = [
  { month: "Jan", awareness: 45, favorability: 32 },
  { month: "Feb", awareness: 50, favorability: 35 },
  { month: "Mar", awareness: 55, favorability: 38 },
  { month: "Apr", awareness: 60, favorability: 42 },
  { month: "May", awareness: 58, favorability: 40 },
  { month: "Jun", awareness: 65, favorability: 45 },
];

export default function DashboardDemo() {
  const [brand, setBrand] = useState("LinkedIn");

  const kpis = [
    { label: "Awareness", value: "65%", color: "#4f46e5" },
    { label: "Favorability", value: "45%", color: "#16a34a" },
    { label: "Consideration", value: "38%", color: "#9333ea" },
    { label: "Conversion", value: "22%", color: "#dc2626" },
  ];

  return (
    <div className="p-6 bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
      <h1 className="text-3xl font-bold mb-6 text-gray-800">
        Consumer Brand Tracker (Live Demo)
      </h1>

      {/* Filters */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <Select onValueChange={setBrand}>
          <SelectItem value="LinkedIn">LinkedIn</SelectItem>
          <SelectItem value="Indeed">Indeed</SelectItem>
          <SelectItem value="Naukri">Naukri</SelectItem>
        </Select>

        <Select>
          <SelectItem value="India">India</SelectItem>
          <SelectItem value="US">US</SelectItem>
        </Select>

        <Select>
          <SelectItem value="Total">Total</SelectItem>
          <SelectItem value="Male">Male</SelectItem>
          <SelectItem value="Female">Female</SelectItem>
        </Select>

        <Button>Apply Filters</Button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {kpis.map((kpi, i) => (
          <motion.div
            key={i}
            whileHover={{ scale: 1.05 }}
            transition={{ duration: 0.2 }}
          >
            <Card className="rounded-2xl shadow-md">
              <CardContent className="p-4">
                <p className="text-sm text-gray-500 uppercase">{kpi.label}</p>
                <p className="text-3xl font-bold" style={{ color: kpi.color }}>
                  {kpi.value}
                </p>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Line Chart */}
      <Card className="rounded-2xl shadow-md">
        <CardContent className="p-4">
          <h2 className="text-lg font-semibold mb-4">Trend Analysis</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={sampleData}>
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="awareness" stroke="#4f46e5" strokeWidth={3} />
              <Line type="monotone" dataKey="favorability" stroke="#16a34a" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
