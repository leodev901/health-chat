'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

type Message = {
  role: 'ai' | 'user';
  content: string;
  time: string;
};

// 루트 페이지: Medical AI Concierge Chat UI 적용
export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'ai',
      content: '안녕하세요! 어떤 도움을 드릴까요? 진료 예약부터 결과 확인까지 실시간으로 도와드립니다.',
      time: new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(`s-${Date.now()}`);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userTime = new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
    const userMessage: Message = { role: 'user', content: input, time: userTime };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const baseUrl = (typeof window !== 'undefined' && (window as any).ENV?.NEXT_PUBLIC_API_BASE_URL) || process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001';
      const response = await fetch(`${baseUrl}/api/agent/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          user_id: 'default_user',
          query: userMessage.content,
        }),
      });

      if (!response.ok) {
        throw new Error('API Error');
      }

      const data = await response.json();

      const aiTime = new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
      const aiMessage: Message = { role: 'ai', content: data.final_answer, time: aiTime };

      setMessages(prev => [...prev, aiMessage]);

    } catch (error) {
      console.error(error);
      const errorTime = new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
      setMessages(prev => [...prev, { role: 'ai', content: '오류가 발생했습니다. 잠시 후 다시 시도해 주세요.', time: errorTime }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  };

  const handleQuickAction = (text: string) => {
    setInput(text);
  };

  return (
    <>
      {/* TopAppBar: 상단 헤더 영역 */}
      <header className="fixed top-0 w-full z-50 bg-white/80 backdrop-blur-md shadow-sm shadow-teal-900/5">
        <div className="flex items-center justify-between px-6 py-4 max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-teal-700" style={{ fontVariationSettings: "'FILL' 0" }}>local_hospital</span>
            <h1 className="font-headline text-teal-800 font-extrabold tracking-tighter text-lg">The Clinical Sanctuary</h1>
          </div>
          <button className="p-2 rounded-full hover:bg-teal-50 transition-colors duration-300 scale-95 active:scale-90">
            <span className="material-symbols-outlined text-slate-500">close</span>
          </button>
        </div>
      </header>

      {/* Main Content Canvas: 메인 컨텐츠 영역 */}
      <main className="pt-24 pb-32 min-h-screen flex flex-col max-w-2xl mx-auto px-4 md:px-0">

        {/* Welcome Section - First Visit Only */}
        {messages.length === 1 && (
          <section className="mb-12 mt-4">
            <h2 className="font-headline text-3xl font-extrabold text-on-surface tracking-tight leading-tight">
              편안한 진료를 위한<br />커스텀 가이드
            </h2>
            <p className="mt-4 text-on-surface-variant font-body text-lg max-w-[80%]">
              클리니컬 생츄어리 AI 어시스턴트입니다. 무엇을 도와드릴까요?
            </p>
          </section>
        )}

        {/* Chat Area: 채팅 및 퀵 액션 영역 */}
        <div className="space-y-8 flex-grow">
          {/* Messages */}
          {messages.map((msg, index) => (
            msg.role === 'ai' ? (
              <div key={index} className="flex flex-col items-start gap-1">
                <div className="flex items-center gap-2 mb-1 pl-1">
                  <div className="w-8 h-8 rounded-full bg-primary-fixed flex items-center justify-center">
                    <span className="material-symbols-outlined text-on-primary-fixed text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>smart_toy</span>
                  </div>
                  <span className="font-label text-xs font-bold uppercase tracking-widest text-primary">Sanctuary AI</span>
                </div>
                <div className="bg-surface-container-highest rounded-xl rounded-tl-none p-5 text-on-surface font-body leading-relaxed max-w-[85%] shadow-sm text-sm space-y-3">
                  <ReactMarkdown 
                    components={{
                      p: ({node, ...props}) => <p className="mb-2 last:mb-0 text-on-surface-variant font-medium break-keep" {...props} />,
                      ul: ({node, ...props}) => <ul className="list-disc pl-5 mb-2 space-y-1 text-on-surface-variant" {...props} />,
                      ol: ({node, ...props}) => <ol className="list-decimal pl-5 mb-2 space-y-1 text-on-surface-variant font-medium" {...props} />,
                      li: ({node, ...props}) => <li className="pl-1 break-keep" {...props} />,
                      strong: ({node, ...props}) => <strong className="font-semibold text-teal-900 dark:text-teal-100" {...props} />,
                      em: ({node, ...props}) => <em className="italic" {...props} />,
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                </div>
                {index > 0 && <span className="text-[10px] text-outline mt-1 px-1">{msg.time}</span>}
              </div>
            ) : (
              <div key={index} className="flex flex-col items-end gap-1 ml-auto max-w-[85%]">
                <div className="bg-primary text-on-primary p-5 rounded-xl rounded-tr-none font-body leading-relaxed shadow-sm whitespace-pre-wrap text-sm">
                  {msg.content}
                </div>
                <span className="text-[10px] text-outline mt-1 px-1">{msg.time}</span>
              </div>
            )
          ))}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex flex-col items-start gap-1">
              <div className="flex items-center gap-2 mb-1 pl-1">
                <div className="w-8 h-8 rounded-full bg-primary-fixed flex items-center justify-center">
                  <span className="material-symbols-outlined text-on-primary-fixed text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>smart_toy</span>
                </div>
                <span className="font-label text-xs font-bold uppercase tracking-widest text-primary">Sanctuary AI</span>
              </div>
              <div className="bg-surface-container-highest rounded-xl rounded-tl-none p-5 text-on-surface font-body leading-relaxed max-w-[85%] shadow-sm">
                <span className="animate-pulse">응답을 생성하는 중입니다...</span>
              </div>
            </div>
          )}

          {/* Quick Action Chips & Information Card - Show only when no active chat */}
          {messages.length === 1 && !isLoading && (
            <>
              <div className="grid grid-cols-2 gap-3 mt-6">
                <button onClick={() => handleQuickAction('진료 예약하고 싶어')} className="flex items-center gap-3 bg-surface-container-lowest p-4 rounded-xl hover:bg-primary-fixed-dim transition-all duration-300 text-left shadow-sm group">
                  <span className="material-symbols-outlined text-primary group-hover:scale-110 transition-transform">calendar_today</span>
                  <span className="font-label text-sm font-semibold">진료 예약</span>
                </button>
                <button onClick={() => handleQuickAction('대기 순번 확인해줘')} className="flex items-center gap-3 bg-surface-container-lowest p-4 rounded-xl hover:bg-primary-fixed-dim transition-all duration-300 text-left shadow-sm group">
                  <span className="material-symbols-outlined text-primary group-hover:scale-110 transition-transform">hourglass_empty</span>
                  <span className="font-label text-sm font-semibold">대기 순번 확인</span>
                </button>
                <button onClick={() => handleQuickAction('진료비 결제')} className="flex items-center gap-3 bg-surface-container-lowest p-4 rounded-xl hover:bg-primary-fixed-dim transition-all duration-300 text-left shadow-sm group">
                  <span className="material-symbols-outlined text-primary group-hover:scale-110 transition-transform">article</span>
                  <span className="font-label text-sm font-semibold">진료비 결제</span>
                </button>
                <button onClick={() => handleQuickAction('입퇴원 안내')} className="flex items-center gap-3 bg-surface-container-lowest p-4 rounded-xl hover:bg-primary-fixed-dim transition-all duration-300 text-left shadow-sm group">
                  <span className="material-symbols-outlined text-primary group-hover:scale-110 transition-transform">article</span>
                  <span className="font-label text-sm font-semibold">입·퇴원 안내</span>
                </button>
              </div>

              <div className="mt-8 relative overflow-hidden rounded-[2rem] bg-surface-container-low p-8 border border-outline-variant/10">
                <div className="relative z-10 flex flex-col gap-2">
                  <h3 className="font-headline font-bold text-lg text-teal-900">당신의 건강 데이터가 암호화되어 보호되고 있습니다.</h3>
                  <p className="font-body text-sm text-on-surface-variant">Clinical Sanctuary는 강력한 보안 프로토콜을 준수합니다.</p>
                </div>
                <div className="absolute -right-4 -bottom-4 w-24 h-24 bg-primary/5 rounded-full blur-2xl"></div>
              </div>
            </>
          )}
        </div>
      </main>

      {/* Floating Input Bar: 하단 메시지 입력창 */}
      <div className="fixed bottom-0 left-0 w-full p-6 z-50 pointer-events-none">
        <div className="max-w-2xl mx-auto w-full pointer-events-auto">
          <div className="relative bg-white/90 backdrop-blur-xl shadow-[0_8px_32px_rgba(0,104,95,0.08)] rounded-full p-2 flex items-center gap-2 border border-outline-variant/10">
            <button className="p-3 text-slate-500 hover:text-teal-600 transition-colors">
              <span className="material-symbols-outlined">add_circle</span>
            </button>
            <input
              className="flex-grow bg-transparent border-none focus:ring-0 font-body text-on-surface placeholder:text-slate-400 py-3 outline-none"
              placeholder="메시지를 입력하세요..."
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <div className="flex items-center gap-1 pr-1">
              <button className="p-3 text-slate-500 hover:text-teal-600 transition-colors rounded-full hover:bg-teal-50">
                <span className="material-symbols-outlined">mic</span>
              </button>
              <button
                onClick={sendMessage}
                disabled={isLoading || !input.trim()}
                className="p-3 bg-primary text-white rounded-full hover:bg-primary-container transition-all active:scale-90 shadow-lg shadow-teal-900/10 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>send</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content Decorative Background Elements: 배경 데코레이션 효과 */}
      <div className="fixed top-0 left-0 w-full h-full -z-10 pointer-events-none overflow-hidden">
        <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] bg-primary-fixed/20 rounded-full blur-[120px]"></div>
        <div className="absolute bottom-[10%] left-[-5%] w-[30%] h-[30%] bg-secondary-fixed/30 rounded-full blur-[100px]"></div>
      </div>
    </>
  );
}
