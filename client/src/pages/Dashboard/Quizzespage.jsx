import React from 'react'
import QuizHistory from '../../components/dashboard/QuizHistory'
import { History } from 'lucide-react'
import Header from '../../components/dashboard/Header'
import { useOutletContext } from 'react-router-dom';

function Quizzespage() {
    const { toggleSidebar } = useOutletContext();
  return (
    <>
         <Header onToggleSidebar={toggleSidebar} />
        {/* Quiz History Section */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-4">
            <History className="h-5 w-5 text-blue-500" />
            <h2 className="text-lg font-semibold ">Quiz History</h2>
          </div>
          <QuizHistory />
        </div>
    </>
        
  )
}

export default Quizzespage