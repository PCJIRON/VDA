import React, { useState, useRef } from 'react';
import { X, Upload, Server, Key, Cpu, FileText, Bot } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

interface SettingsModalProps {
  onClose: () => void;
}

type Tab = 'ai' | 'mcp' | 'skills';

export function SettingsModal({ onClose }: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<Tab>('ai');
  const [provider, setProvider] = useState("OpenAI");
  const [model, setModel] = useState("gpt-4o");
  const [customModel, setCustomModel] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [mcpServer, setMcpServer] = useState("");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setUploadedFile(e.target.files[0]);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
      />
      <motion.div 
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        className="relative bg-[#1e1e24] border border-neutral-800 rounded-2xl w-full max-w-3xl h-[500px] text-white shadow-2xl overflow-hidden flex flex-row-reverse"
      >
        {/* Right Sidebar (Drawer) */}
        <div className="w-56 bg-[#151518] border-l border-neutral-800/50 p-4 flex flex-col">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-neutral-500">Settings</h2>
            <button onClick={onClose} className="p-1.5 -mr-1.5 text-neutral-400 hover:text-white rounded-lg hover:bg-neutral-800 transition-colors">
              <X size={18} />
            </button>
          </div>
          
          <nav className="space-y-1">
            <button 
              onClick={() => setActiveTab('ai')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${activeTab === 'ai' ? 'bg-blue-600/10 text-blue-400' : 'text-neutral-400 hover:bg-neutral-800 hover:text-neutral-200'}`}
            >
              <Cpu size={18} /> AI Provider
            </button>
            <button 
              onClick={() => setActiveTab('mcp')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${activeTab === 'mcp' ? 'bg-blue-600/10 text-blue-400' : 'text-neutral-400 hover:bg-neutral-800 hover:text-neutral-200'}`}
            >
              <Server size={18} /> MCP Server
            </button>
            <button 
              onClick={() => setActiveTab('skills')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${activeTab === 'skills' ? 'bg-blue-600/10 text-blue-400' : 'text-neutral-400 hover:bg-neutral-800 hover:text-neutral-200'}`}
            >
              <FileText size={18} /> Skills
            </button>
          </nav>

          <div className="mt-auto">
            <button onClick={onClose} className="w-full py-2.5 rounded-xl text-sm font-medium bg-white text-black hover:bg-neutral-200 transition-colors">
              Save & Close
            </button>
          </div>
        </div>

        {/* Left Content Area */}
        <div className="flex-1 p-8 overflow-y-auto">
          <AnimatePresence mode="wait">
            {activeTab === 'ai' && (
              <motion.div 
                key="ai"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                transition={{ duration: 0.2 }}
                className="space-y-6 max-w-md"
              >
                <div>
                  <h3 className="text-xl font-semibold mb-1">AI Provider</h3>
                  <p className="text-sm text-neutral-400 mb-6">Configure your preferred AI model and API keys.</p>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-neutral-300">Provider</label>
                  <select 
                    value={provider}
                    onChange={(e) => setProvider(e.target.value)}
                    className="w-full bg-[#141418] border border-neutral-700 rounded-lg px-3 py-2.5 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all text-sm appearance-none"
                  >
                    <option>OpenAI</option>
                    <option>Anthropic</option>
                    <option>Gemini</option>
                    <option>Local</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-neutral-300">Model</label>
                  <select 
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    className="w-full bg-[#141418] border border-neutral-700 rounded-lg px-3 py-2.5 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all text-sm appearance-none"
                  >
                    <option value="gpt-4o">GPT-4o</option>
                    <option value="gpt-4-turbo">GPT-4 Turbo</option>
                    <option value="claude-3-opus">Claude 3 Opus</option>
                    <option value="claude-3-sonnet">Claude 3.5 Sonnet</option>
                    <option value="custom">Custom (Manual)</option>
                  </select>
                  
                  <AnimatePresence>
                    {model === "custom" && (
                      <motion.input 
                        initial={{ opacity: 0, height: 0, marginTop: 0 }}
                        animate={{ opacity: 1, height: 'auto', marginTop: 12 }}
                        exit={{ opacity: 0, height: 0, marginTop: 0 }}
                        type="text"
                        placeholder="Enter custom model ID (e.g. llama-3-70b)"
                        value={customModel}
                        onChange={(e) => setCustomModel(e.target.value)}
                        className="w-full bg-[#141418] border border-neutral-700 rounded-lg px-3 py-2.5 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all text-sm placeholder:text-neutral-600"
                      />
                    )}
                  </AnimatePresence>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-neutral-300">API Key</label>
                  <input 
                    type="password"
                    placeholder="Enter your API key..."
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    className="w-full bg-[#141418] border border-neutral-700 rounded-lg px-3 py-2.5 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all text-sm placeholder:text-neutral-600"
                  />
                </div>
              </motion.div>
            )}

            {activeTab === 'mcp' && (
              <motion.div 
                key="mcp"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                transition={{ duration: 0.2 }}
                className="space-y-6 max-w-md"
              >
                <div>
                  <h3 className="text-xl font-semibold mb-1">MCP Server</h3>
                  <p className="text-sm text-neutral-400 mb-6">Connect to an external Model Context Protocol server.</p>
                </div>
                
                <div className="space-y-2">
                  <label className="text-sm font-medium text-neutral-300">Server URL</label>
                  <input 
                    type="text"
                    placeholder="http://localhost:3000/mcp"
                    value={mcpServer}
                    onChange={(e) => setMcpServer(e.target.value)}
                    className="w-full bg-[#141418] border border-neutral-700 rounded-lg px-3 py-2.5 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all text-sm placeholder:text-neutral-600"
                  />
                </div>
              </motion.div>
            )}

            {activeTab === 'skills' && (
              <motion.div 
                key="skills"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                transition={{ duration: 0.2 }}
                className="space-y-6 max-w-md"
              >
                <div>
                  <h3 className="text-xl font-semibold mb-1">Agent Skills</h3>
                  <p className="text-sm text-neutral-400 mb-6">Upload custom skills for your AI agent to use.</p>
                </div>

                <div className="space-y-2">
                  <input 
                    type="file" 
                    accept=".md"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    className="hidden" 
                  />
                  <div 
                    onClick={() => fileInputRef.current?.click()}
                    className={`border-2 border-dashed ${uploadedFile ? 'border-blue-500/50 bg-blue-500/5' : 'border-neutral-700 hover:border-neutral-500 bg-[#141418]'} rounded-xl p-8 flex flex-col items-center justify-center text-center transition-colors cursor-pointer group`}
                  >
                    {uploadedFile ? (
                      <>
                        <FileText size={32} className="text-blue-400 mb-4" />
                        <p className="text-sm text-blue-200 font-medium">{uploadedFile.name}</p>
                        <p className="text-xs text-blue-400/70 mt-1">{(uploadedFile.size / 1024).toFixed(1)} KB</p>
                      </>
                    ) : (
                      <>
                        <Upload size={32} className="text-neutral-500 mb-4 group-hover:text-neutral-300 transition-colors" />
                        <p className="text-sm text-neutral-300 font-medium">Upload skills.md</p>
                        <p className="text-xs text-neutral-500 mt-2">Drag and drop or click to browse</p>
                      </>
                    )}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
}