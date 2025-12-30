"use client";

import { useRouter } from "next/navigation";
import { Sparkles, Plus, Upload, FileSearch } from "lucide-react";

export default function AICommand() {
  const router = useRouter();

  const handleStartInvestigation = () => {
    router.push("/dashboard/search");
  };

  const handleUploadIntel = () => {
    router.push("/dashboard/vault");
  };

  const handleViewPendingRequests = () => {
    router.push("/dashboard/requests");
  };

  return (
    <div className="h-full bg-glass-light backdrop-blur-md border border-glass-border rounded-2xl p-8 flex flex-col">
      <div className="flex items-center justify-between mb-6 h-14">
        <h2 className="text-sm font-bold tracking-wider text-gray-400 flex items-center">
          AI COMMAND
        </h2>
        <button className="text-gray-500 hover:text-white transition-colors flex items-center h-6">
          •••
        </button>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center text-center space-y-8">
        <div className="w-16 h-16 rounded-full bg-gradient-to-br from-cyber-cyan to-cyber-purple flex items-center justify-center shadow-glow-cyan relative">
          <Sparkles className="w-8 h-8 text-white absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
        </div>

        <div className="space-y-2 w-full">
          <h3 className="text-2xl font-thin text-white text-center">WELCOME, MAJOR V. SINGH.</h3>
          <p className="text-lg text-cyber-cyan font-medium text-center">SYSTEM IS READY.</p>
        </div>

        <div className="grid grid-cols-3 gap-4 w-full">
          <button 
            onClick={handleStartInvestigation}
            className="flex flex-col items-center gap-2 p-4 rounded-xl bg-glass-medium border border-glass-border hover:border-cyber-cyan/50 hover:bg-glass-light transition-all group cursor-pointer"
          >
            <div className="w-10 h-10 rounded-lg bg-space-200 flex items-center justify-center group-hover:bg-cyber-cyan/10 transition-colors">
              <Plus className="w-5 h-5 text-gray-400 group-hover:text-cyber-cyan transition-colors" />
            </div>
            <span className="text-xs font-medium text-gray-400 group-hover:text-white transition-colors text-center leading-tight">
              START NEW INVESTIGATION
            </span>
          </button>

          <button 
            onClick={handleUploadIntel}
            className="flex flex-col items-center gap-2 p-4 rounded-xl bg-glass-medium border border-glass-border hover:border-cyber-purple/50 hover:bg-glass-light transition-all group cursor-pointer"
          >
            <div className="w-10 h-10 rounded-lg bg-space-200 flex items-center justify-center group-hover:bg-cyber-purple/10 transition-colors">
              <Upload className="w-5 h-5 text-gray-400 group-hover:text-cyber-purple transition-colors" />
            </div>
            <span className="text-xs font-medium text-gray-400 group-hover:text-white transition-colors text-center leading-tight">
              UPLOAD INTEL
            </span>
          </button>

          <button 
            onClick={handleViewPendingRequests}
            className="flex flex-col items-center gap-2 p-4 rounded-xl bg-glass-medium border border-glass-border hover:border-cyber-green/50 hover:bg-glass-light transition-all group cursor-pointer"
          >
            <div className="w-10 h-10 rounded-lg bg-space-200 flex items-center justify-center group-hover:bg-cyber-green/10 transition-colors">
              <FileSearch className="w-5 h-5 text-gray-400 group-hover:text-cyber-green transition-colors" />
            </div>
            <span className="text-xs font-medium text-gray-400 group-hover:text-white transition-colors text-center leading-tight">
              VIEW PENDING REQUESTS
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}

