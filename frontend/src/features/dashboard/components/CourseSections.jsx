import { Link } from "react-router-dom";
import { CaretLeft, ChatCircleText, GlobeHemisphereEast } from "@phosphor-icons/react";
import SectionCard from "./SectionCard";

const sectionsData = [
  {
    id: 1,
    title: "Section 1",
    status: "completed",
    details: "see details",
  },
  {
    id: 2,
    title: "Section 2",
    status: "completed",
    details: "see details",
  },
  {
    id: 3,
    title: "Section 3",
    status: "completed",
    details: "see details",
  },
  {
    id: 4,
    title: "Section 4",
    status: "current",
    progress: 70,
    details: "In Progress",
    illustration: {
      text: "사람들과 한국어로 조금 대화할 수 있어요.",
      Icon: ChatCircleText,
      color: "#1cb0f6",
    }
  },
  {
    id: 5,
    title: "Section 5",
    status: "locked",
    units: 250,
    details: "LOCKED",
    illustration: {
      text: "한국어로 일상 생활이 가능해요.",
      Icon: GlobeHemisphereEast,
      color: "#58cc02",
    }
  },
  {
    id: 6,
    title: "Section 6",
    status: "locked",
    units: 250,
    details: "LOCKED",
    illustration: {
      text: "상황에 따라 한국어로 그에 맞는 표현을 할 수 있어요.",
      Icon: ChatCircleText,
      color: "#7848f4",
    }
  },
  {
    id: 7,
    title: "Section 7",
    status: "locked",
    units: 200,
    details: "LOCKED",
    illustration: {
      text: "나의 희망, 목표, 계획과 같은 추상적 주제에 대해 말할 수 있어요.",
      Icon: GlobeHemisphereEast,
      color: "#ff9600",
    }
  },
  {
    id: 8,
    title: "Section 8",
    status: "locked",
    units: 200,
    details: "LOCKED",
    illustration: {
      text: "한국어를 편하게 할 수 있어요. 다양한 주제에 대해 자연스럽게 내 의견을 말할 수 있어요.",
      Icon: ChatCircleText,
      color: "#ff4b4b",
    }
  },
  {
    id: 9,
    title: "Daily Refresh",
    status: "locked",
    units: 0,
    details: "6 LEVELS",
    subtitle: "Complete the course to unlock this section!"
  }
];

const CourseSections = () => {
  return (
    <div className="flex flex-col gap-2 max-w-[1056px] mx-auto pb-20">
      <div className="mb-6 flex items-center border-b-2 border-[#e5e5e5] pb-4 px-4 sticky top-0 bg-white/10 backdrop-blur-md z-20">
        <Link 
          to="/learn" 
          className="flex items-center gap-2 text-[#afafaf] hover:text-[#777777] transition-colors"
        >
          <CaretLeft size={20} weight="bold" />
          <span className="font-black uppercase tracking-wide">Back</span>
        </Link>
      </div>

      <div className="flex flex-col">
        {sectionsData.map((section) => (
          <SectionCard 
            key={section.id}
            section={section}
            isCompleted={section.status === "completed"}
            isActive={section.status === "current"}
            isLocked={section.status === "locked"}
          />
        ))}
      </div>
    </div>
  );
};

export default CourseSections;
