"use client";

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const data = [
  { date: "Mar 1", weight: 80 },
  { date: "Mar 8", weight: 82.5 },
  { date: "Mar 15", weight: 85 },
  { date: "Mar 22", weight: 85 },
  { date: "Mar 29", weight: 87.5 },
  { date: "Apr 5", weight: 90 },
];

export default function ProgressChart() {
  return (
    <div className="p-6 rounded-xl border border-white/10 bg-white/[0.02] col-span-full h-80">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-sm font-medium text-white/50">Estimated 1RM Progress</h3>
        <select className="bg-white/5 border border-white/10 rounded-md text-sm px-2 py-1 text-white focus:outline-none">
          <option>Bench Press</option>
          <option>Squat</option>
          <option>Deadlift</option>
        </select>
      </div>
      
      <div className="w-full h-48">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
            <XAxis 
              dataKey="date" 
              stroke="#ffffff50" 
              fontSize={12} 
              tickLine={false}
              axisLine={false}
            />
            <YAxis 
              stroke="#ffffff50" 
              fontSize={12} 
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `${value}kg`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#000",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: "8px",
              }}
              itemStyle={{ color: "#fff" }}
            />
            <Line
              type="monotone"
              dataKey="weight"
              stroke="#fff"
              strokeWidth={2}
              dot={{ fill: "#000", stroke: "#fff", strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, fill: "#fff" }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
