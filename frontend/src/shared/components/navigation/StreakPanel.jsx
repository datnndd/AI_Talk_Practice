import { useState } from 'react';
import { CaretLeft, CaretRight } from '@phosphor-icons/react';

const StreakPanel = () => {
  const [currentMonthIndex, setCurrentMonthIndex] = useState(1);

  const months = [
    { name: 'March 2026', days: 31, offset: 0 },
    { name: 'April 2026', days: 30, offset: 3 },
    { name: 'May 2026', days: 31, offset: 5 },
  ];

  const currentMonth = months[currentMonthIndex];

  return (
    <div className="flex flex-col gap-4">
      <div className="app-panel bg-white p-5 cursor-default">
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm font-black text-[#4b4b4b] uppercase tracking-wider">Calendar</span>
          <div className="flex gap-2">
            <button 
              onClick={() => setCurrentMonthIndex(prev => Math.max(0, prev - 1))}
              disabled={currentMonthIndex === 0}
              className="p-1 rounded-lg hover:bg-[#f7f7f7] disabled:opacity-30"
            >
              <CaretLeft weight="bold" size={16} />
            </button>
            <button 
              onClick={() => setCurrentMonthIndex(prev => Math.min(months.length - 1, prev + 1))}
              disabled={currentMonthIndex === months.length - 1}
              className="p-1 rounded-lg hover:bg-[#f7f7f7] disabled:opacity-30"
            >
              <CaretRight weight="bold" size={16} />
            </button>
          </div>
        </div>

        <div className="text-center">
          <div className="text-sm font-black text-[#afafaf] mb-4">{currentMonth.name}</div>
          
          <div className="streak-calendar-grid mb-2">
            {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map(day => (
              <div key={day} className="text-[11px] font-black text-[#afafaf]">{day}</div>
            ))}
          </div>

          <div className="streak-calendar-grid">
            {Array.from({ length: currentMonth.offset }).map((_, i) => (
              <div key={`empty-${i}`} className="calendar-day"></div>
            ))}
            {Array.from({ length: currentMonth.days }).map((_, i) => {
              const dayNum = i + 1;
              const isToday = currentMonthIndex === 1 && dayNum === 21; // April 21st mock as today
              return (
                <div key={dayNum} className={`calendar-day ${isToday ? 'active' : ''}`}>
                  {dayNum}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default StreakPanel;
