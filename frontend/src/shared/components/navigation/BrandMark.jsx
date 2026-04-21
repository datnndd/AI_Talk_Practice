import { Link } from "react-router-dom";

const BrandMark = ({ to = "/", compact = false }) => {
  return (
    <Link to={to} className="group inline-flex items-center gap-2">
      <div className={`flex items-center text-duo-text transition duration-300 group-hover:scale-[1.03] ${compact ? 'scale-75 origin-left' : ''}`}>
        <svg 
          className="w-8 h-8 mr-2 text-duo-text" 
          fill="none" 
          viewBox="0 0 24 24" 
          xmlns="http://www.w3.org/2000/svg"
        >
          <path 
            d="M21 11.5C21 15.6421 17.1944 19 12.5 19C11.5284 19 10.6015 18.854 9.74233 18.5833L5 21V16.634C3.16339 15.2638 2 13.4866 2 11.5C2 7.35786 5.80558 4 10.5 4C15.1944 4 19 7.35786 19 11.5" 
            stroke="currentColor" 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth="2"
          />
          <circle cx="7" cy="11" fill="currentColor" r="1" />
          <circle cx="11" cy="11" fill="currentColor" r="1" />
          <circle cx="15" cy="11" fill="currentColor" r="1" />
        </svg>
        <span className="text-2xl font-bold tracking-tight text-duo-text">
          SpeakEasy <span className="text-duo-green">AI</span>
        </span>
      </div>
    </Link>
  );
};

export default BrandMark;
