export default function ReadinessGauge({ score = 85 }: { score?: number }) {
  let colorClass = "text-green-500 text-shadow-green";
  let statusText = "Primed for PR";
  
  if (score < 50) {
    colorClass = "text-red-500 text-shadow-red";
    statusText = "High Fatigue";
  } else if (score < 80) {
    colorClass = "text-yellow-500 text-shadow-yellow";
    statusText = "Moderate Fatigue";
  }

  return (
    <div className="p-6 rounded-xl border border-white/10 bg-white/[0.02]">
      <h3 className="text-sm font-medium text-white/50 mb-4">Daily Readiness</h3>
      
      <div className="flex items-center justify-between">
        <div>
          <div className={`text-4xl font-bold ${colorClass}`}>
            {score}
            <span className="text-lg text-white/30 font-medium">/100</span>
          </div>
          <p className="text-sm text-white/70 mt-1">{statusText}</p>
        </div>
        
        <div className="relative w-16 h-16 flex items-center justify-center">
          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
            <path
              className="text-white/10"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className={colorClass.split(" ")[0]}
              strokeDasharray={`${score}, 100`}
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none"
              stroke="currentColor"
              strokeWidth="4"
            />
          </svg>
        </div>
      </div>
    </div>
  );
}
